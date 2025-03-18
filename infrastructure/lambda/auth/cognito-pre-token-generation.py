import os
import logging
from typing import Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
TABLE_NAME = os.environ['TABLE_NAME']

# AWS clients initialization
dynamodb = boto3.client('dynamodb')

class TenantNotFoundError(Exception):
    """Custom exception for missing tenant"""
    pass

class UserAccessDeniedError(Exception):
    """Custom exception for user access denied"""
    pass

def query_tenant_id_by_user_sub(sub: str) -> Optional[str]:
    """
    Search for Tenant ID associated with User Sub
    
    Args:
        sub: Cognito User sub identifier
        
    Returns:
        Optional[str]: Tenant ID if found, None otherwise
        
    Raises:
        ClientError: When DynamoDB operation fails
    """
        
    try:
        response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={
                ':pk': {'S': f'membership#{sub}'}
            }
        )
        
        items = response.get('Items', [])
        if items:
            return items[0]['sk']['S'].replace('tenant#', '')
        return None
        
    except ClientError as e:
        logger.warning(f"Error querying tenant ID: {str(e)}")
        raise

def validate_event(event: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Validate and extract required data from event
    
    Args:
        event: Lambda event
        
    Returns:
        Tuple: (user_pool_id, app_client_id, sub)
        
    Raises:
        ValueError: When required fields are missing
    """
    try:
        user_pool_id = event['userPoolId']
        app_client_id = event['callerContext']['clientId']
        sub = event['request']['userAttributes']['sub']
        return user_pool_id, app_client_id, sub
    except KeyError as e:
        logger.warning(f"Missing required field in event: {str(e)}")
        raise ValueError(f"Missing required field: {str(e)}")

def add_claims_to_event(event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """
    Add tenant_id claim to Cognito event
    
    Args:
        event: Lambda event
        tenant_id: Tenant identifier
        
    Returns:
        Dict: Updated event with claims
    """
    event['response'] = {
        'claimsOverrideDetails': {
            'claimsToAddOrOverride': {
                'tenant_id': tenant_id
            }
        }
    }
    return event

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Cognito Pre Token Generation
    
    Args:
        event: Lambda event containing Cognito user information
        context: Lambda context
        
    Returns:
        Dict: Modified event with tenant_id claim
        
    Raises:
        RuntimeError: When user access is not allowed or unexpected errors occur
    """
    try:
        # Validate and extract event data
        user_pool_id, app_client_id, sub = validate_event(event)
        logger.info(
            f"Processing request for user_pool_id: {user_pool_id}, "
            f"app_client_id: {app_client_id}, sub: {sub}"
        )
        
        # Get Tenant ID
        tenant_id = query_tenant_id_by_user_sub(sub)
        if not tenant_id:
            logger.warning("Tenant not found")
            raise TenantNotFoundError("Tenant Not Found")
        
        # Add claims to event
        return add_claims_to_event(event, tenant_id)
        
    except TenantNotFoundError:
        logger.warning(f"Tenant not found for user: {sub}")
        raise RuntimeError("Tenant association not found")
    except UserAccessDeniedError:
        logger.warning(f"Access denied for user: {sub}")
        raise RuntimeError("User access denied")
    except Exception as e:
        logger.warning(f"Unexpected error in handler: {str(e)}")
        raise RuntimeError("Authentication process failed")
