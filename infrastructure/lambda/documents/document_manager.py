import json
import os
import logging
import boto3
import requests
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'opensearch-rag-app')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')

# Constants
CORS_HEADERS = {
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Access-Control-Allow-Origin,Access-Control-Allow-Credentials',
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGINS', '*'),
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    'Access-Control-Allow-Credentials': 'true',
    'Content-Type': 'application/json'
}

def create_response(status_code: int, body: Any) -> Dict[str, Any]:
    """
    Create standardized API response
    
    Args:
        status_code: HTTP status code
        body: Response body (dict or message string)
        
    Returns:
        Dict: Formatted API response
    """
    if isinstance(body, str):
        body = {'message': body}
    
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

def format_file_size(size_in_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_in_bytes: File size in bytes
        
    Returns:
        str: Formatted file size
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

def get_aos_domain_and_index(tenant_id: str, sub: str) -> Tuple[str, str]:
    """
    Get OpenSearch domain and index
    
    Args:
        tenant_id: Tenant identifier
        sub: User subject identifier
        
    Returns:
        Tuple: OpenSearch domain and index name
        
    Raises:
        ValueError: When configuration is missing or invalid
    """
    try:
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={
                'pk': {'S': f'tenant#{tenant_id}'},
                'sk': {'S': 'os_config'}
            }
        )
        item = response.get('Item')
        if not item:
            raise ValueError(f"No configuration found for tenant {tenant_id} and user {sub}")
            
        opensearch_domain = item.get('os_host', {}).get('S')
        index_name = item.get('os_index', {}).get('S')
        
        if not opensearch_domain or not index_name:
            raise ValueError("Missing required OpenSearch configuration")
            
        return opensearch_domain, index_name
    except Exception as e:
        logger.warning(f"Error getting OpenSearch configuration: {str(e)}")
        raise

def get_file_type(filename: str) -> str:
    """
    Get file type from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        str: File type
    """
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if extension in ['pdf']:
        return 'PDF'
    elif extension in ['doc', 'docx']:
        return 'Word'
    elif extension in ['txt']:
        return 'Text'
    elif extension in ['csv', 'xls', 'xlsx']:
        return 'Spreadsheet'
    else:
        return extension.upper() if extension else 'Unknown'

def delete_document_from_opensearch(doc_id: str, token: str, opensearch_domain: str, index_name: str) -> Dict[str, Any]:
    """
    Delete document from OpenSearch
    
    Args:
        doc_id: Document ID
        token: Authorization token
        opensearch_domain: OpenSearch domain
        index_name: OpenSearch index name
        
    Returns:
        Dict: OpenSearch response
        
    Raises:
        requests.exceptions.RequestException: When OpenSearch request fails
    """
    url = f'https://{opensearch_domain}/{index_name}/_doc/{doc_id}'
    headers = {'Authorization': token}

    try:
        # Set timeout to prevent indefinite waiting
        response = requests.delete(url, headers=headers, timeout=(3.0, 10.0))
        
        if response.status_code == 404:
            logger.warning(f"Document {doc_id} not found in OpenSearch")
            return {"status": "not_found"}
            
        response.raise_for_status()
        logger.info(f"OpenSearch delete response: status={response.status_code}, body={response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        # Changed from error to warning since we're propagating the exception
        logger.warning(f"Error deleting document from OpenSearch: {str(e)}")
        raise

def verify_cognito_jwt(token: str) -> dict:
    """
    Verify Cognito JWT token and return claims
    
    Args:
        token: JWT token string (with or without 'Bearer ' prefix)
        
    Returns:
        dict: JWT claims
        
    Raises:
        ValueError: When token verification fails
    """
    # Remove Bearer prefix if present
    if token.startswith('Bearer '):
        token = token.replace('Bearer ', '')
        
    # Get Cognito configuration from environment variables
    region = os.environ.get('AWS_REGION', 'us-west-2')
    userpool_id = USER_POOL_ID
    app_client_id = USER_POOL_CLIENT_ID
    
    if not userpool_id or not app_client_id:
        logger.warning("Missing required environment variables: USER_POOL_ID or USER_POOL_CLIENT_ID")
        raise ValueError("Missing Cognito configuration")
    
    # Construct JWKS URL
    keys_url = f'https://cognito-idp.{region}.amazonaws.com/{userpool_id}/.well-known/jwks.json'
    
    try:
        # Get public keys using requests instead of urllib
        response = requests.get(keys_url, timeout=3.0)
        response.raise_for_status()
        keys = response.json()['keys']
        
        # Get kid from token header
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        
        # Find matching public key
        key_index = -1
        for i in range(len(keys)):
            if kid == keys[i]['kid']:
                key_index = i
                break
                
        if key_index == -1:
            logger.warning('Public key not found in jwks.json')
            raise ValueError('Invalid token: Public key not found')
            
        # Construct public key
        public_key = jwk.construct(keys[key_index])
        
        # Split token into message and signature parts
        message, encoded_signature = str(token).rsplit('.', 1)
        
        # Decode signature
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        
        # Verify signature
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            logger.warning('Signature verification failed')
            raise ValueError('Invalid token: Signature verification failed')
            
        # Get claims from token
        claims = jwt.get_unverified_claims(token)
        
        # Verify token expiration
        if time.time() > claims['exp']:
            logger.warning('Token is expired')
            raise ValueError('Invalid token: Token is expired')
            
        # Verify audience (for access tokens)
        if 'aud' in claims and claims['aud'] != app_client_id:
            logger.warning('Token was not issued for this audience')
            raise ValueError('Invalid token: Invalid audience')
            
        # Verify client_id (for ID tokens)
        if 'client_id' in claims and claims['client_id'] != app_client_id:
            logger.warning('Token was not issued for this client')
            raise ValueError('Invalid token: Invalid client')
            
        logger.info('JWT token successfully verified')
        return claims
        
    except Exception as e:
        logger.warning(f"JWT verification error: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")

def get_documents(tenant_id: str) -> List[Dict[str, Any]]:
    """
    Get documents for a tenant
    
    Args:
        tenant_id: Tenant identifier
        
    Returns:
        List: List of documents
    """
    response = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression='pk = :pk AND begins_with(sk, :sk_prefix)',
        ExpressionAttributeValues={
            ':pk': {'S': f'tenant#{tenant_id}'},
            ':sk_prefix': {'S': 'documents#'}
        }
    )
    
    items = response.get('Items', [])
    formatted_items = []
    
    for item in items:
        formatted_items.append({
            'id': item['uniqueId']['S'],
            'title': item['fileName']['S'],
            'uploadDate': item['uploadedAt']['S'],
            'fileType': get_file_type(item['fileName']['S']),
            'size': format_file_size(int(item['fileSize']['N'])),
            'bucket': item['bucket']['S'],
            'key': item['key']['S'],
            'status': item['status']['S']
        })
    
    return formatted_items

def delete_document(tenant_id: str, sub: str, unique_id: str, token: str) -> None:
    """
    Delete document from OpenSearch, S3, and DynamoDB
    
    Args:
        tenant_id: Tenant identifier
        sub: User subject identifier
        unique_id: Document unique ID
        token: Authorization token
        
    Raises:
        ValueError: When document is not found
    """
    # Get record from DynamoDB
    response = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            'pk': {'S': f'tenant#{tenant_id}'},
            'sk': {'S': f'documents#{unique_id}'}
        }
    )
    
    if 'Item' not in response:
        raise ValueError("Document not found")
    
    item = response['Item']

    # Get OpenSearch domain/index
    opensearch_domain, index_name = get_aos_domain_and_index(tenant_id, sub)

    # Delete document from OpenSearch
    delete_document_from_opensearch(unique_id, token, opensearch_domain, index_name)
    
    # Delete file from S3
    s3.delete_object(
        Bucket=item['bucket']['S'],
        Key=item['key']['S']
    )
    
    # Delete record from DynamoDB
    dynamodb.delete_item(
        TableName=TABLE_NAME,
        Key={
            'pk': {'S': f'tenant#{tenant_id}'},
            'sk': {'S': f'documents#{unique_id}'}
        }
    )

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document management
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Dict: API Gateway response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    http_method = event['httpMethod']
    
    # Handle OPTIONS request for CORS
    if http_method == 'OPTIONS':
        return create_response(200, "")
    
    # Extract and validate JWT token
    try:
        auth_header = event['headers'].get('Authorization', '')
        if not auth_header:
            return create_response(401, "Missing authorization header")
            
        # Verify JWT token
        decoded_jwt = verify_cognito_jwt(auth_header)
        tenant_id = decoded_jwt.get("tenant_id")
        sub = decoded_jwt.get("sub")
        
        if not tenant_id or not sub:
            logger.warning("Missing required claims in token")
            return create_response(401, "Invalid token: Missing required claims")
    except Exception as e:
        return create_response(401, f"Authentication failed: {str(e)}")
    
    if http_method == 'GET':
        try:
            formatted_items = get_documents(tenant_id)
            return create_response(200, formatted_items)
        except Exception as e:
            logger.warning(f"Error retrieving documents: {str(e)}")
            return create_response(500, f"Error retrieving documents: {str(e)}")
    
    elif http_method == 'DELETE':
        try:
            body = json.loads(event['body'])
            unique_id = body['id']  # Unique ID sent from frontend
            
            delete_document(tenant_id, sub, unique_id, auth_header)
            return create_response(200, "Document deleted successfully")
        except ValueError as e:
            logger.warning(f"Value error: {str(e)}")
            return create_response(400, str(e))
        except requests.exceptions.RequestException as e:
            logger.warning(f"OpenSearch error: {str(e)}")
            return create_response(500, f"Error deleting document from OpenSearch: {str(e)}")
        except Exception as e:
            logger.warning(f"Error deleting document: {str(e)}")
            return create_response(500, f"Error deleting document: {str(e)}")
    
    else:
        return create_response(405, f"Method {http_method} not allowed")