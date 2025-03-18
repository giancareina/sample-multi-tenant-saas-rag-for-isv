import os
import json
import logging
import boto3
import requests
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from prompt_templates import RAG_PROMPT_TEMPLATE

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
EMBEDDING_MODEL_ID = os.getenv('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v2:0')
REGION = os.getenv('AWS_REGION', 'us-west-2')
TABLE_NAME = os.environ['TABLE_NAME']
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')

# AWS clients initialization
dynamodb = boto3.client('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)

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

def create_response(status_code: int, message: str, sources: Optional[list] = None) -> Dict[str, Any]:
    """
    Create standardized API response
    
    Args:
        status_code: HTTP status code
        message: Response message
        sources: Optional list of sources used in the response
        
    Returns:
        Dict: Formatted API response
    """
    body = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'sources': sources if sources else []
    }
    
    logger.info(f"Response body: {json.dumps(body)}")
    
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

def get_aos_domain_and_index(tenant_id: str, sub: str) -> Tuple[str, str]:
    """
    Get OpenSearch domain and index information
    
    Args:
        tenant_id: Tenant identifier
        sub: User subject identifier
        
    Returns:
        Tuple: OpenSearch domain and index name
        
    Raises:
        ValueError: When configuration is missing
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

def get_embedding(text: str) -> list:
    """
    Get text embedding from Bedrock
    
    Args:
        text: Input text
        
    Returns:
        list: Embedding vector
        
    Raises:
        Exception: When embedding generation fails
    """
    try:
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            body=json.dumps({"inputText": text}),
            contentType="application/json"
        )
        return json.loads(response['body'].read())['embedding']
    except Exception as e:
        logger.warning(f"Error getting embedding: {str(e)}")
        raise

def vector_search(
    index_name: str,
    opensearch_domain: str,
    embedded_query: list,
    headers: dict,
    limit: int = 1
) -> Tuple[Optional[str], Optional[list]]:
    """
    Execute vector search in OpenSearch
    
    Args:
        index_name: OpenSearch index name
        opensearch_domain: OpenSearch domain
        embedded_query: Query embedding vector
        headers: Request headers
        limit: Number of results to return
        
    Returns:
        Tuple[Optional[str], Optional[list]]: Search results text and sources or None if failed
    """
    search_body = {
        "size": limit,
        "query": {
            "nested": {
                "score_mode": "max",
                "path": "embedding",
                "query": {
                    "knn": {
                        "embedding.knn": {
                            "vector": embedded_query,
                            "k": limit
                        }
                    }
                },
            }
        }
    }

    url = f'https://{opensearch_domain}/{index_name}/_search'

    try:
        response = requests.get(url, json=search_body, headers=headers, timeout=(3.05, 27))
        response.raise_for_status()
        data = response.json()
        
        # Log search results count
        hit_count = len(data['hits']['hits'])
        logger.info(f"Vector search found {hit_count} results")
        
        # Extract content and build sources list
        content = ""
        sources = []
        
        for hit in data['hits']['hits']:
            source = hit.get('_source', {})
            # Use body field from the document
            body_content = source.get('body', '')
            content += body_content + "\n\n"
            
            # Add source metadata
            sources.append({
                'title': 'Document',
                'snippet': body_content[:200] + '...' if body_content else '',
                'metadata': {'tenant_id': source.get('tenant_id', 'unknown')}
            })
        
        # Log response data for debugging
        logger.info(f"Vector search response data: {json.dumps(data['hits']['hits'])}")
        
        return content, sources if sources else None
    except Exception as e:
        logger.warning(f"Vector search error: {str(e)}")
        return None, None

def generate_response_with_converse(prompt: str, conversation_history: list = None) -> str:
    """
    Generate response using Bedrock Converse API
    
    Args:
        prompt: Input prompt
        conversation_history: List of previous conversation messages
        
    Returns:
        str: Generated response
        
    Raises:
        Exception: When generation fails
    """
    try:
        messages = []
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get('role'),
                    "content": [{"text": msg.get('content')}]
                })
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": [{"text": prompt}]
        })
        
        inference_config = {'temperature': 1.0, 'topP': 1.0, 'maxTokens': 1024}
        
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        try:
            content = response.get('output', {}).get('message', {}).get('content', [])
            return ''.join(item.get('text', '') for item in content)
        except Exception as content_error:
            logger.warning(f"Error parsing Bedrock response: {str(content_error)}")
            return "I'm sorry, I couldn't generate a proper response."
    except Exception as e:
        logger.warning(f"Response generation error: {str(e)}")
        raise

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler"""
    # Log that function was called without exposing sensitive data
    logger.info("Chat completion handler called")
    
    # Validate input
    if not event.get('headers') or not event.get('headers').get('Authorization'):
        return create_response(401, "Missing authorization header")
        
    if not event.get('body'):
        return create_response(400, "Missing request body")

    try:
        # Parse and verify JWT token
        token = event['headers']['Authorization']
        
        try:
            # Verify JWT token in Lambda in addition to API Gateway verification
            decoded_jwt = verify_cognito_jwt(token)
            tenant_id = decoded_jwt.get("tenant_id")
            sub = decoded_jwt.get("sub")
            
            if not tenant_id or not sub:
                logger.warning("Missing required claims in token")
                return create_response(401, "Invalid token: Missing required claims")
                
        except ValueError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return create_response(401, f"Authentication failed: {str(e)}")

        # Get OpenSearch configuration
        opensearch_domain, index_name = get_aos_domain_and_index(tenant_id, sub)

        # Process query and conversation history
        body = json.loads(event['body'])
        query_text = body.get('message')
        conversation_history = body.get('conversationHistory', [])
        
        # Always use knowledge base for queries
        context = None
        sources = None
        
        # Get embeddings and search OpenSearch
        embedded_query = get_embedding(query_text)
        headers = {'Authorization': token, 'Content-Type': 'application/json'}
        context, sources = vector_search(index_name, opensearch_domain, embedded_query, headers, limit=5)
        
        context = context or ''

        # Generate response using RAG with conversation history
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, query=query_text)
        
        # Call generate_response_with_converse with both prompt and conversation history
        answer = generate_response_with_converse(prompt, conversation_history)
        
        response = create_response(200, answer, sources)
        
        return response

    except Exception as e:
        logger.warning(f"Error in handler: {str(e)}")
        return create_response(500, 'An internal error occurred. Please try again later.')