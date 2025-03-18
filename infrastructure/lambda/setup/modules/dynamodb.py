import boto3
from datetime import datetime
from typing import Dict, Any

def save_tenant_to_dynamodb(tenant: str, tenant_config: Dict[str, Dict[str, str]], 
                          table_name: str, user_sub: str) -> None:
    """Save tenant information to DynamoDB"""
    try:
        dynamodb = boto3.client('dynamodb')
        
        # Save tenant configuration
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'pk': {'S': f'tenant#{tenant}'},
                'sk': {'S': 'os_config'},
                'os_host': {'S': tenant_config[tenant]['domain']},
                'os_index': {'S': tenant_config[tenant]['index']},
                'rag_role': {'S': f'{tenant}_role'},
            }
        )

        # Save user and tenant association
        dynamodb.put_item(
            TableName=table_name,
            Item={
                "pk": {"S": f"membership#{user_sub}"},  # use sub
                "sk": {"S": f"tenant#{tenant}"}
            }
        )
        
    except Exception as e:
        raise ValueError(f"Failed to save tenant to DynamoDB: {str(e)}")