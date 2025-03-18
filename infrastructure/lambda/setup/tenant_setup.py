import json
import os
import traceback
from typing import Dict, Any

# Import modules
from modules import (
    setup_jwt_authentication, 
    setup_cognito_for_tenant,
    get_awsauth, 
    create_ingest_pipeline, 
    setup_opensearch_for_tenant,
    get_tenant_config, 
    validate_environment,
    save_tenant_to_dynamodb
)

def create_single_tenant_resources(
    tenant: str,
    tenant_config: Dict[str, Dict[str, str]],
    user_pool_id: str,
    user_password: str,
    cognito_appclient: str,
    table_name: str,
    aws_auth: Any,
    pipeline_name: str
) -> Dict[str, Any]:
    """Create resources for single tenant"""
    try:
        # Configure Cognito
        cognito_info = setup_cognito_for_tenant(tenant, user_pool_id, user_password)
        
        # Configure OpenSearch
        setup_opensearch_for_tenant(tenant, tenant_config, aws_auth, pipeline_name)
        
        # Configure DynamoDB
        save_tenant_to_dynamodb(tenant, tenant_config, table_name, cognito_info['sub'])
        
        return {
            'tenant': tenant,
            'email': cognito_info['email'],
            'password': cognito_info['password'],
            'app_client_id': cognito_appclient,
            'membership_id': cognito_info['sub']
        }
    except Exception as e:
        raise

def create_tenant_resources(
    domain_a: str,
    domain_b: str,
    user_pool_id: str,
    cognito_appclient: str,
    table_name: str,
    user_password: str
) -> Dict[str, Any]:
    """Main function to create tenant resources"""
    try:
        aws_auth = get_awsauth(os.environ['AWS_REGION'], 'es')
        
        # Create ingest pipeline
        pipeline_name = create_ingest_pipeline(domain_a, domain_b, aws_auth)
        
        # Tenant configuration and creation process
        tenant_config = get_tenant_config()
        results = []
        
        for tenant in tenant_config.keys():
            try:
                result = create_single_tenant_resources(
                    tenant=tenant,
                    tenant_config=tenant_config,
                    user_pool_id=user_pool_id,
                    user_password=user_password,
                    cognito_appclient=cognito_appclient,
                    table_name=table_name,
                    aws_auth=aws_auth,
                    pipeline_name=pipeline_name
                )
                results.append(result)
            except Exception as e:
                raise

        # Configure JWT authentication
        for domain in [domain_a, domain_b]:
            setup_jwt_authentication(domain, aws_auth, user_pool_id, user_password)
            
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'trace': traceback.format_exc()
            })
        }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler"""
    try:
        validate_environment()
        
        request_type = event['RequestType']
        
        if request_type == 'Create':
            response = create_tenant_resources(
                domain_a=os.environ['OPENSEARCH_DOMAIN_A'],
                domain_b=os.environ['OPENSEARCH_DOMAIN_B'],
                user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                cognito_appclient=os.environ['COGNITO_APP_CLIENT_ID'],
                table_name=os.environ['TABLE_NAME'],
                user_password=os.environ['DEMO_USER_PASSWORD']
            )
        else:
            response = {
                'statusCode': 200,
                'body': f'{request_type} request ignored'
            }
            
        return {
            'PhysicalResourceId': f'tenant-resources-{os.environ["COGNITO_USER_POOL_ID"]}',
            'Status': 'SUCCESS' if response['statusCode'] == 200 else 'FAILED',
            'Reason': response.get('body', 'No reason provided'),
            'Data': {
                'Message': response.get('body', 'Operation completed')
            }
        }
            
    except Exception as e:
        return {
            'PhysicalResourceId': event.get('PhysicalResourceId', 'error'),
            'Status': 'FAILED',
            'Reason': str(e),
            'Data': {
                'Error': str(e),
                'Trace': traceback.format_exc()
            }
        }