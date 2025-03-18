import json
import os
import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ClientError
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
import uuid
from typing import Dict, Any, Optional, Tuple
import requests

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
REGION = os.environ['AWS_REGION']
BUCKET_NAME = os.environ['FILE_BUCKET']
URL_EXPIRATION = 300  # 5 minutes

# AWS clients initialization
s3_client = boto3.client(
    's3',
    config=Config(signature_version='s3v4'),
    region_name=REGION,
    endpoint_url=f'https://s3.{REGION}.amazonaws.com'
)

# CORS headers definition
CORS_HEADERS = {
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Access-Control-Allow-Origin,Access-Control-Allow-Credentials',
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGINS', '*'),
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT',
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

def validate_request_parameters(params: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate request parameters
    
    Args:
        params: Query string parameters
        
    Returns:
        Tuple: (file_name, file_type) if valid, (None, None) if invalid
    """
    file_name = params.get('fileName')
    file_type = params.get('fileType')
    
    if not file_name or not file_type:
        return None, None
    return file_name, file_type

def generate_presigned_url(
    bucket: str,
    object_key: str,
    file_type: str,
    original_filename: str
) -> str:
    """
    Generate presigned URL for S3 upload
    
    Args:
        bucket: S3 bucket name
        object_key: S3 object key
        file_type: File content type
        original_filename: Original file name
        
    Returns:
        str: Presigned URL
        
    Raises:
        ClientError: When S3 operation fails
    """
    try:
        return s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': object_key,
                'ContentType': file_type,
                'Metadata': {'original_filename': original_filename}
            },
            ExpiresIn=URL_EXPIRATION,
            HttpMethod='PUT'
        )
    except ClientError as e:
        # Not only log the error, but also handle it here using ERROR level
        # When propagating the error, use WARNING level to record detailed information
        logger.warning(f"Error generating presigned URL: {str(e)}")
        raise



def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for presigned URL generation
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Dict: API response
        
    Raises:
        Exception: When processing fails
    """
    try:
        # Validate authorization
        if 'Authorization' not in event.get('headers', {}):
            return create_response(401, {'error': 'Missing authorization header'})
            
        # Verify JWT token
        token = event['headers']['Authorization']
        
        try:
            # Verify JWT token in Lambda in addition to API Gateway verification
            decoded_jwt = verify_cognito_jwt(token)
            tenant_id = decoded_jwt.get("tenant_id")
            sub = decoded_jwt.get("sub")
            
            if not tenant_id or not sub:
                logger.warning("Missing required claims in token")
                return create_response(401, {'error': 'Invalid token: Missing required claims'})
                
        except ValueError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return create_response(401, {'error': f'Authentication failed: {str(e)}'})
        
        # Validate request parameters
        file_name, file_type = validate_request_parameters(
            event.get('queryStringParameters', {})
        )
        if not file_name or not file_type:
            return create_response(400, {
                'error': 'fileName and fileType are required query parameters'
            })
        
        # Generate unique identifier and object key
        unique_id = str(uuid.uuid4())
        object_key = f"{tenant_id}/{unique_id}"
        
        # Generate presigned URL
        signed_url = generate_presigned_url(
            bucket=BUCKET_NAME,
            object_key=object_key,
            file_type=file_type,
            original_filename=file_name
        )
        
        logger.info(f"Generated presigned URL for tenant: {tenant_id}, file: {file_name}")
        
        return create_response(200, {
            'signedUrl': signed_url,
            'objectKey': object_key,
            'uniqueId': unique_id
        })
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return create_response(400, f"Invalid request parameters: {str(e)}")
    except ClientError as e:
        logger.warning(f"AWS client error: {str(e)}")
        return create_response(500, "Failed to generate signed URL")
    except Exception as e:
        logger.warning(f"Unexpected error: {str(e)}")
        return create_response(500, "Internal server error")