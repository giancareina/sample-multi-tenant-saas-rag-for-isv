import boto3
import os
import jwt
import requests
from typing import Dict, Any
from base64 import urlsafe_b64decode
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def base64url_decode(input: str) -> bytes:
    """Decode Base64URL encoded string"""
    padding = '=' * (4 - (len(input) % 4))
    return urlsafe_b64decode(input + padding)

def jwk_to_pem(jwk):
    """Convert JWK to PEM format"""
    e = int.from_bytes(base64url_decode(jwk['e']), byteorder='big')
    n = int.from_bytes(base64url_decode(jwk['n']), byteorder='big')
    
    # Generate Base64 encoded string of RSA public key
    numbers = RSAPublicNumbers(e, n)
    public_key = numbers.public_key(backend=default_backend())
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return pem.strip()  # Remove trailing newlines

def safe_request(method: str, url: str, **kwargs) -> requests.Response:
    """Execute HTTP request safely and provide detailed error information"""
    try:
        # Set timeout to prevent indefinite waiting
        # connect_timeout: connection establishment timeout, read_timeout: response reception timeout
        response = requests.request(method, url, timeout=(3.0, 30.0), **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {str(e)}")

def setup_jwt_authentication(domain: str, aws_auth: Any, user_pool_id: str, user_password: str) -> None:
    """Configure JWT authentication for OpenSearch"""
    try:        
        # Create Cognito client and perform authentication for testing
        cognito_client = boto3.client('cognito-idp')
        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=os.environ['COGNITO_APP_CLIENT_ID'],
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'tenant-a-user',
                'PASSWORD': user_password
            }
        )
        
        id_token = auth_response['AuthenticationResult']['IdToken']
        
        # Get kid from ID token
        token_header = jwt.get_unverified_header(id_token)
        token_kid = token_header['kid']
        
        # Get JWKS
        region = os.environ['AWS_REGION']
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        response = safe_request('GET', jwks_url)
        jwks = response.json()
        
        # Identify JWK corresponding to ID token
        signing_key = None
        for key in jwks['keys']:
            if key['kid'] == token_kid:
                signing_key = key
                break
                
        if not signing_key:
            raise ValueError(f"No matching JWK found for kid: {token_kid}")
                    
        # Create OpenSearch Service client
        opensearch_client = boto3.client('opensearch')
        
        # Extract domain name
        domain_name = "-".join(domain.split('.')[0].replace('vpc-', '').split('-')[:2])
        
        # Configure JWT authentication
        opensearch_client.update_domain_config(
            DomainName=domain_name,
            AdvancedSecurityOptions={
                'JWTOptions': {
                    'Enabled': True,
                    'RolesKey': 'tenant_id',
                    'SubjectKey': 'sub',
                    'PublicKey': jwk_to_pem(signing_key)
                }
            }
        )
        
    except Exception as e:
        raise ValueError(f"Failed to setup JWT authentication: {str(e)}")

def setup_cognito_for_tenant(tenant: str, user_pool_id: str, user_password: str) -> Dict[str, str]:
    """Configure Cognito settings for tenant"""
    try:
        cognito_client = boto3.client('cognito-idp')
        email = f'{tenant}@example.com'
        permanent_password = user_password
        username = f'{tenant}-user'
        
        # Create user and get sub from response
        create_user_response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username, 
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
            ],
            TemporaryPassword=permanent_password,
            MessageAction='SUPPRESS'
        )
        
        # Get sub
        user_sub = None
        for attr in create_user_response['User']['Attributes']:
            if attr['Name'] == 'sub':
                user_sub = attr['Value']
                break
        
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,  
            Password=permanent_password,
            Permanent=True
        )
        
        return {
            'email': email,
            'password': permanent_password,
            'sub': user_sub
        }
        
    except Exception as e:
        raise ValueError(f"Failed to setup Cognito for tenant {tenant}: {str(e)}")