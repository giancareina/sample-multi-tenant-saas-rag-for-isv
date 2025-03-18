import json
import os
import boto3
import logging
from typing import Tuple, Optional, Dict, Any
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
import requests

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
TABLE_NAME = os.environ['TABLE_NAME']

# AWS clients initialization
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')

# CORS headers definition
CORS_HEADERS = {
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Access-Control-Allow-Origin,Access-Control-Allow-Credentials',
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGINS', '*'),
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    'Access-Control-Allow-Credentials': 'true',
    'Content-Type': 'application/json'
}

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
    userpool_id = os.environ.get('USER_POOL_ID')
    app_client_id = os.environ.get('USER_POOL_CLIENT_ID')
    
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

def get_aos_domain_and_index(tenant_id: str, sub: str) -> Tuple[str, str]:
    """
    Get OpenSearch domain and index
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


def read_csv_from_s3(bucket: str, key: str) -> str:
    """
    Read CSV content from S3
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        str: CSV content as string
    """
    # Get object from S3
    obj = s3.get_object(Bucket=bucket, Key=key)
    
    # Read object body and store as string
    csv_content = obj['Body'].read().decode('utf-8')  # Decode as UTF-8
    
    return csv_content

def put_document_to_opensearch(doc_id: str, content: str, token: str, opensearch_domain: str, index_name: str, tenant_id: str) -> Dict[str, Any]:
    """
    Put document to OpenSearch
    
    Args:
        doc_id: Document ID
        content: Document content
        token: Authorization token
        opensearch_domain: OpenSearch domain
        index_name: OpenSearch index name
        tenant_id: Tenant ID
        
    Returns:
        Dict: API response
        
    Raises:
        requests.exceptions.RequestException: When OpenSearch request fails
    """
    request_body = {
        "body": content,
        "tenant_id": tenant_id
    }

    url = f'https://{opensearch_domain}/{index_name}/_doc/{doc_id}'
    headers = {'Authorization': token, 'Content-Type': 'application/json'}

    try:
        # Set timeout to prevent indefinite waiting
        response = requests.put(url, json=request_body, headers=headers, timeout=(3.0, 10.0))
        response.raise_for_status()
        logger.info(f"OpenSearch put response: status={response.status_code}, body={response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error putting document to OpenSearch: {str(e)}")
        raise

def get_document_info(tenant_id: str, doc_id: str) -> Dict[str, Any]:
    """
    Get document information from DynamoDB
    
    Args:
        tenant_id: Tenant ID
        doc_id: Document ID
        
    Returns:
        Dict: Document information
        
    Raises:
        ValueError: When document is not found
    """
    response = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            'pk': {'S': f'tenant#{tenant_id}'},
            'sk': {'S': f'documents#{doc_id}'}
        }
    )

    if 'Item' not in response:
        raise ValueError(f"Document not found: {doc_id}")

    return response['Item']

def update_document_status(tenant_id: str, doc_id: str, status: str) -> None:
    """
    Update document status in DynamoDB
    
    Args:
        tenant_id: Tenant ID
        doc_id: Document ID
        status: New status
    """
    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            'pk': {'S': f'tenant#{tenant_id}'},
            'sk': {'S': f'documents#{doc_id}'}
        },
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': {'S': status}
        }
    )

def process_document(tenant_id: str, sub: str, doc_id: str, token: str) -> None:
    """
    Process document: read from S3 and upload to OpenSearch
    
    Args:
        tenant_id: Tenant ID
        sub: User subject ID
        doc_id: Document ID
        token: Authorization token
        
    Raises:
        ValueError: When document is not found
        Exception: When processing fails
    """
    # Get document info
    item = get_document_info(tenant_id, doc_id)
    bucket = item['bucket']['S']
    key = item['key']['S']

    # Check if file exists in S3
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            raise ValueError(f"File not found in S3: {doc_id}")
        raise

    # Update status to syncing
    update_document_status(tenant_id, doc_id, 'syncing')

    try:
        # Read CSV file from S3
        content = read_csv_from_s3(bucket, key)

        # Get OpenSearch domain/index
        opensearch_domain, index_name = get_aos_domain_and_index(tenant_id, sub)

        # Put document to OpenSearch
        put_document_to_opensearch(doc_id, content, token, opensearch_domain, index_name, tenant_id)

        # Update status after successful processing
        update_document_status(tenant_id, doc_id, 'synced')
    except Exception as e:
        # Update status on error
        update_document_status(tenant_id, doc_id, 'error')
        raise

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document syncing
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Dict: API Gateway response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Handle preflight request
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {})

        # Get token from headers
        token = event['headers']['Authorization']
        
        try:
            # Verify JWT token
            decoded_jwt = verify_cognito_jwt(token)
            tenant_id = decoded_jwt.get("tenant_id")
            sub = decoded_jwt.get("sub")
            
            if not tenant_id or not sub:
                logger.warning("Missing required claims in token")
                return create_response(401, {'message': 'Invalid token: Missing required claims'})
                
        except ValueError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return create_response(401, {'message': f'Authentication failed: {str(e)}'})

        # Parse request body
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        doc_id = body.get('docId')

        if not doc_id:
            return create_response(400, {'message': 'docId is required'})

        # Process document
        try:
            process_document(tenant_id, sub, doc_id, token)
        except ValueError as e:
            return create_response(404, {
                'message': str(e),
                'docId': doc_id
            })
        except Exception as e:
            logger.warning(f"Error processing document: {str(e)}")
            return create_response(500, {
                'message': 'An error occurred while processing the document',
                'docId': doc_id
            })

        # Response for async processing start
        return create_response(202, {
            'message': 'Document processing started',
            'docId': doc_id
        })

    except json.JSONDecodeError:
        return create_response(400, "Invalid JSON in request body")
    except Exception as e:
        logger.warning(f"Error processing document: {str(e)}")
        error_message = {
            'message': 'An internal error occurred while processing the document',
            'docId': body.get('docId') if 'body' in locals() and isinstance(body, dict) else None
        }
        return create_response(500, error_message)