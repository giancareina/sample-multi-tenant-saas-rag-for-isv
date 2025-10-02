import os
import json
import logging
from typing import Dict, Any, Optional, List
import boto3
from jose import jwk, jwt
from jose.utils import base64url_decode
import time
import requests

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

dynamodb = boto3.client('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')

def create_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Create standardized API response.
    
    Args:
        status_code: HTTP status code
        body: Response body
        headers: Optional headers
        
    Returns:
        Dict: Lambda response format
    """
    # Get allowed origin from environment variable
    allowed_origin = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173')
    
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }

def get_dashboard_data(tenant_id: str) -> Dict[str, Any]:
        """
        Get current month dashboard data for a tenant by aggregating individual usage events.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict: Dashboard data
        """
        try:
            logger.info(f"Fetching dashboard data for tenant {tenant_id}")
            
            usage_events = []
        
            logger.info(f"Looking for any usage events with pk prefix: tenant#{tenant_id}#usage#")
            
            scan_kwargs = {
                'TableName': TABLE_NAME,
                'FilterExpression': 'begins_with(pk, :pk_prefix)',
                'ExpressionAttributeValues': {
                    ':pk_prefix': {'S': f'tenant#{tenant_id}#usage#'}
                }
            }
            
            # Handle pagination
            while True:
                response = dynamodb.scan(**scan_kwargs)
                    
                # Convert DynamoDB items to Python dicts
                for item in response.get('Items', []):
                    event = convert_dynamodb_item(item)
                    usage_events.append(event)
                
                # Check if there are more items to scan
                if 'LastEvaluatedKey' not in response:
                    break
                    
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            
            logger.info(f"Retrieved {len(usage_events)} usage events for tenant {tenant_id}")
            
            if not usage_events:
                logger.warning(f"No usage events found for tenant {tenant_id}")
                
                # Return zero values if no data found
                return {
                    'current_month': {
                        'total_cost': 0.0,
                        'total_invocations': 0,
                        'total_tokens': 0,
                        'chat_invocations': 0,
                        'embedding_invocations': 0,
                        'model_breakdown': {}
                    },
                    'trends': {
                        'cost_trend': 0.0,
                        'usage_trend': 0.0
                    }
                }
            
            # Aggregate the usage events into dashboard metrics
            dashboard_metrics = aggregate_usage_events(usage_events)
            
            logger.info(f"Aggregated metrics: {dashboard_metrics['total_invocations']} invocations, ${dashboard_metrics['total_cost']:.6f} cost")
            
            # Structure data according to frontend expectations
            dashboard_data = {
                'current_month': dashboard_metrics,
            }
            
            logger.info(f"Generated dashboard data for tenant {tenant_id}: {dashboard_metrics['total_cost']:.6f} USD, {dashboard_metrics['total_invocations']} invocations")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for tenant {tenant_id}: {str(e)}")
            raise

def aggregate_usage_events(usage_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate individual usage events into dashboard metrics.
        
        Args:
            usage_events: List of usage events
            
        Returns:
            Dict: Aggregated metrics
        """
        try:
            total_cost = 0.0
            total_invocations = 0
            total_tokens = 0
            chat_invocations = 0
            embedding_invocations = 0
            model_breakdown = {}
            
            for event in usage_events:
                # Extract event data
                model_type = event.get('model_type', '')
                model_id = event.get('model_id', '')
                input_tokens = event.get('input_tokens', 0)
                output_tokens = event.get('output_tokens', 0)
                event_total_tokens = event.get('total_tokens', input_tokens + output_tokens)
                estimated_cost = event.get('estimated_cost', 0.0)
                
                # Aggregate totals
                total_cost += estimated_cost
                total_invocations += 1
                total_tokens += event_total_tokens
                
                # Count by model type
                if model_type == 'chat':
                    chat_invocations += 1
                elif model_type == 'embedding':
                    embedding_invocations += 1
                
                # Model-specific breakdown
                if model_id not in model_breakdown:
                    model_breakdown[model_id] = {
                        'invocations': 0,
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'cost': 0.0
                    }
                
                model_breakdown[model_id]['invocations'] += 1
                model_breakdown[model_id]['input_tokens'] += input_tokens
                model_breakdown[model_id]['output_tokens'] += output_tokens
                model_breakdown[model_id]['cost'] += estimated_cost
            
            return {
                'total_cost': round(total_cost, 10),
                'total_invocations': total_invocations,
                'total_tokens': total_tokens,
                'chat_invocations': chat_invocations,
                'embedding_invocations': embedding_invocations,
                'model_breakdown': model_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error aggregating usage events: {str(e)}")
            return {
                'total_cost': 0.0,
                'total_invocations': 0,
                'total_tokens': 0,
                'chat_invocations': 0,
                'embedding_invocations': 0,
                'model_breakdown': {}
            }

def convert_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert DynamoDB item format to Python dict.
        
        Args:
            item: DynamoDB item
            
        Returns:
            Dict: Converted Python dict
        """
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = float(value['N']) if '.' in value['N'] else int(value['N'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
            elif 'M' in value:
                # Handle nested maps (like model_breakdown)
                result[key] = {}
                for sub_key, sub_value in value['M'].items():
                    if 'M' in sub_value:
                        # Nested map (model breakdown)
                        result[key][sub_key] = convert_dynamodb_item({'nested': sub_value})['nested']
                    elif 'N' in sub_value:
                        result[key][sub_key] = float(sub_value['N']) if '.' in sub_value['N'] else int(sub_value['N'])
                    elif 'S' in sub_value:
                        result[key][sub_key] = sub_value['S']
        
        return result
    
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

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for consumption metering API.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Dict: API response
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Extract tenant ID from JWT
        token = event['headers']['Authorization']
        
        # Verify JWT token in Lambda in addition to API Gateway verification
        decoded_jwt = verify_cognito_jwt(token)
        tenant_id = decoded_jwt.get("tenant_id")

        if not tenant_id:
            return create_response(401, {'error': 'Unable to extract tenant ID from authorization token'})
        
        # Route based on path and method
        path = event.get('path', '')
        method = event.get('httpMethod', 'GET')
        
        if path.endswith('/dashboard') and method == 'GET':
            # Get dashboard data
            logger.info(f"Processing dashboard request for tenant: {tenant_id}")
            try:
                dashboard_data = get_dashboard_data(tenant_id)
                logger.info(f"Dashboard data generated successfully: {json.dumps(dashboard_data, default=str)}")
                
                return create_response(200, dashboard_data)
            except Exception as dashboard_error:
                logger.error(f"Error generating dashboard data: {str(dashboard_error)}", exc_info=True)
                return create_response(500, {'error': 'Failed to generate dashboard data', 'details': str(dashboard_error)})
        
        else:
            return create_response(404, {'error': f'Endpoint not found: {method} {path}'})
    
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})