import boto3
import json
import uuid
import os
from typing import Dict, Any, Optional
from requests_aws4auth import AWS4Auth
import requests
from .config import load_config

def get_awsauth(region: str, service: str) -> AWS4Auth:
    """Create AWS authentication object"""
    credentials = boto3.Session().get_credentials()
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )

def execute_opensearch_operation(
    domain: str,
    operation_name: str,
    aws_auth: AWS4Auth,
    path_params: Dict[str, str] = None,
    payload_updates: Dict[str, Any] = None
) -> Optional[str]:
    """Common function for OpenSearch operations"""
    try:
        operations = load_config('config/opensearch_operations.json')
        
        if operation_name not in operations:
            raise ValueError(f"Unknown operation: {operation_name}")
            
        operation = operations[operation_name]
        path = operation['path']
        
        # Replace path parameters
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", value)
                
        url = f"https://{domain}{path}"
        
        # Prepare payload
        payload = None
        if 'payload' in operation:
            payload = operation['payload'].copy()
            if payload_updates:
                deep_merge(payload, payload_updates)
        else:
            payload = payload_updates
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if 'headers' in operation:
            headers.update(operation['headers'])
        
        response = requests.request(
            operation['method'],
            url,
            auth=aws_auth,
            json=payload if payload else None,
            headers=headers,
            timeout=(3.0, 30.0)
        )
        response.raise_for_status()
        
        if 'response_key' in operation:
            result = response.json().get(operation['response_key'])
            return result
        
        return None
        
    except Exception as e:
        raise ValueError(f"OpenSearch operation failed: {str(e)}")

def deep_merge(base: Dict, update: Dict) -> None:
    """Perform deep merge of dictionaries"""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

def get_dls_query(tenant: str) -> str:
    """Generate DLS query"""
    dls_query = {
        "bool": {
            "must": {
                "match": {
                    "tenant_id": tenant
                }
            }
        }
    }
    return json.dumps(dls_query)

def get_role_definition(tenant_config: Dict[str, Dict[str, str]], tenant: str) -> Dict[str, Any]:
    """Get tenant role definitions"""
    if tenant == 'tenant-a':
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": ["*"],
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    elif tenant == 'tenant-b':
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": [f"{tenant_config[tenant]['index']}*"],
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    elif tenant in ['tenant-c', 'tenant-d']:
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": [f"{tenant_config[tenant]['index']}*"],
                "dls": get_dls_query(tenant),
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    return role_definition

def create_ingest_pipeline(domain_a: str, domain_b: str, aws_auth: AWS4Auth) -> str:
    """Create ingest pipeline"""
    try:
        pipeline_name = "text-embedding-pipeline"
        
        # Configure ML Plugin
        for domain in [domain_a, domain_b]:
            execute_opensearch_operation(domain, "ml_plugin", aws_auth)
        
        # Configure connector
        connector_updates = {
            "parameters": {
                "service_name": "bedrock",
                "region": os.environ['AWS_REGION'],
                "role_arn": os.environ['BEDROCK_ACCESS_ROLE']
            },
            "credential": {
                "roleArn": os.environ['BEDROCK_ACCESS_ROLE']
            }
        }
        
        # Create connector
        connector_id_a = execute_opensearch_operation(
            domain_a,
            "connector",
            aws_auth,
            payload_updates=connector_updates
        )
        connector_id_b = execute_opensearch_operation(
            domain_b,
            "connector",
            aws_auth,
            payload_updates=connector_updates
        )
        
        # Create model group (unique name)
        model_group_name = f"remote_model_group_{uuid.uuid4()}"
        model_group_updates = {
            "name": model_group_name,
            "description": "Remote model group for Bedrock"
        }
        
        model_group_id_a = execute_opensearch_operation(
            domain_a,
            "model_group",
            aws_auth,
            payload_updates=model_group_updates
        )
        
        model_group_id_b = execute_opensearch_operation(
            domain_b,
            "model_group",
            aws_auth,
            payload_updates=model_group_updates
        )
        
        # Register model
        register_updates_a = {
            "model_group_id": model_group_id_a,
            "connector_id": connector_id_a
        }
        task_id_a = execute_opensearch_operation(
            domain_a,
            "model_register",
            aws_auth,
            payload_updates=register_updates_a
        )
        
        register_updates_b = {
            "model_group_id": model_group_id_b,
            "connector_id": connector_id_b
        }
        task_id_b = execute_opensearch_operation(
            domain_b,
            "model_register",
            aws_auth,
            payload_updates=register_updates_b
        )
        
        # Get model id
        model_id_a = execute_opensearch_operation(
            domain_a,
            "get_model_id",
            aws_auth,
            path_params={"task_id": task_id_a}
        )
        
        model_id_b = execute_opensearch_operation(
            domain_b,
            "get_model_id",
            aws_auth,
            path_params={"task_id": task_id_b}
        )
        
        # Deploy model and create pipeline
        for domain, model_id in [(domain_a, model_id_a), (domain_b, model_id_b)]:
            execute_opensearch_operation(
                domain,
                "model_deploy",
                aws_auth,
                path_params={"model_id": model_id}
            )
            
            execute_opensearch_operation(
                domain,
                "pipeline",
                aws_auth,
                path_params={"pipeline_name": pipeline_name},
                payload_updates={"processors": [{"text_embedding": {"model_id": model_id}}]}
            )
            
        return pipeline_name
        
    except Exception as e:
        raise ValueError(f"Failed to create ingest pipeline: {str(e)}")

def setup_opensearch_for_tenant(tenant: str, tenant_config: Dict[str, Dict[str, str]], 
                              aws_auth: AWS4Auth, pipeline_name: str) -> None:
    """Configure OpenSearch settings for tenant"""
    try:
        # Create KNN index
        if tenant != 'tenant-d':
            execute_opensearch_operation(
                tenant_config[tenant]['domain'],
                "create_knn_index",
                aws_auth,
                path_params={"index_name": tenant_config[tenant]['index']},
                payload_updates={
                    "settings": {
                        "index": {
                            "knn.space_type": "cosinesimil",
                            "default_pipeline": pipeline_name,
                            "knn": "true"
                        }
                    }
                }
            )
        
        # Create roles
        role_definition = get_role_definition(tenant_config, tenant)
        execute_opensearch_operation(
            tenant_config[tenant]['domain'],
            "create_role",
            aws_auth,
            path_params={"role_name": f"{tenant}_role"},
            payload_updates=role_definition
        )
        
        # Create role mappings
        role_mapping = {"backend_roles": [tenant]}
        execute_opensearch_operation(
            tenant_config[tenant]['domain'],
            "create_role_mapping",
            aws_auth,
            path_params={"role_name": f"{tenant}_role"},
            payload_updates=role_mapping
        )
    except Exception as e:
        raise ValueError(f"Failed to setup OpenSearch for tenant {tenant}: {str(e)}")

def get_dls_query(tenant: str) -> str:
    """Generate DLS query"""
    dls_query = {
        "bool": {
            "must": {
                "match": {
                    "tenant_id": tenant
                }
            }
        }
    }
    return json.dumps(dls_query)

def get_role_definition(tenant_config: Dict[str, Dict[str, str]], tenant: str) -> Dict[str, Any]:
    """Get tenant role definitions"""
    if tenant == 'tenant-a':
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": ["*"],
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    elif tenant == 'tenant-b':
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": [f"{tenant_config[tenant]['index']}*"],
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    elif tenant in ['tenant-c', 'tenant-d']:
        role_definition = {
            "cluster_permissions": ["cluster_composite_ops", "cluster:admin/opensearch/ml/predict"],
            "index_permissions": [{
                "index_patterns": [f"{tenant_config[tenant]['index']}*"],
                "dls": get_dls_query(tenant),
                "allowed_actions": ["write", "read", "search"]
            }]
        }
    return role_definition

def create_ingest_pipeline(domain_a: str, domain_b: str, aws_auth: AWS4Auth) -> str:
    """Create ingest pipeline"""
    try:
        pipeline_name = "text-embedding-pipeline"
        
        # Configure ML Plugin
        for domain in [domain_a, domain_b]:
            execute_opensearch_operation(domain, "ml_plugin", aws_auth)
        
        # Configure connector
        connector_updates = {
            "parameters": {
                "service_name": "bedrock",
                "region": os.environ['AWS_REGION'],
                "role_arn": os.environ['BEDROCK_ACCESS_ROLE']
            },
            "credential": {
                "roleArn": os.environ['BEDROCK_ACCESS_ROLE']
            }
        }
        
        # Create connector
        connector_id_a = execute_opensearch_operation(
            domain_a,
            "connector",
            aws_auth,
            payload_updates=connector_updates
        )
        connector_id_b = execute_opensearch_operation(
            domain_b,
            "connector",
            aws_auth,
            payload_updates=connector_updates
        )
        
        # Create model group (unique name)
        model_group_name = f"remote_model_group_{uuid.uuid4()}"
        model_group_updates = {
            "name": model_group_name,
            "description": "Remote model group for Bedrock"
        }
        
        model_group_id_a = execute_opensearch_operation(
            domain_a,
            "model_group",
            aws_auth,
            payload_updates=model_group_updates
        )
        
        model_group_id_b = execute_opensearch_operation(
            domain_b,
            "model_group",
            aws_auth,
            payload_updates=model_group_updates
        )
        
        # Register model
        register_updates_a = {
            "model_group_id": model_group_id_a,
            "connector_id": connector_id_a
        }
        task_id_a = execute_opensearch_operation(
            domain_a,
            "model_register",
            aws_auth,
            payload_updates=register_updates_a
        )
        
        register_updates_b = {
            "model_group_id": model_group_id_b,
            "connector_id": connector_id_b
        }
        task_id_b = execute_opensearch_operation(
            domain_b,
            "model_register",
            aws_auth,
            payload_updates=register_updates_b
        )
        
        # Get model id
        model_id_a = execute_opensearch_operation(
            domain_a,
            "get_model_id",
            aws_auth,
            path_params={"task_id": task_id_a}
        )
        
        model_id_b = execute_opensearch_operation(
            domain_b,
            "get_model_id",
            aws_auth,
            path_params={"task_id": task_id_b}
        )
        
        # Deploy model and create pipeline
        for domain, model_id in [(domain_a, model_id_a), (domain_b, model_id_b)]:
            execute_opensearch_operation(
                domain,
                "model_deploy",
                aws_auth,
                path_params={"model_id": model_id}
            )
            
            # Get pipeline configuration from opensearch_operations.json
            operations = load_config('config/opensearch_operations.json')
            pipeline_payload = operations.get('pipeline', {}).get('payload', {})
            
            # Update the model_id in the pipeline configuration
            if 'processors' in pipeline_payload and len(pipeline_payload['processors']) > 1:
                if 'text_embedding' in pipeline_payload['processors'][1]:
                    pipeline_payload['processors'][1]['text_embedding']['model_id'] = model_id
            
            execute_opensearch_operation(
                domain,
                "pipeline",
                aws_auth,
                path_params={"pipeline_name": pipeline_name},
                payload_updates=pipeline_payload
            )
            
        return pipeline_name
        
    except Exception as e:
        raise ValueError(f"Failed to create ingest pipeline: {str(e)}")

def setup_opensearch_for_tenant(tenant: str, tenant_config: Dict[str, Dict[str, str]], 
                              aws_auth: AWS4Auth, pipeline_name: str) -> None:
    """Configure OpenSearch settings for tenant"""
    try:
        # Create KNN index
        if tenant != 'tenant-d':
            execute_opensearch_operation(
                tenant_config[tenant]['domain'],
                "create_knn_index",
                aws_auth,
                path_params={"index_name": tenant_config[tenant]['index']},
                payload_updates={
                    "settings": {
                        "index": {
                            "knn.space_type": "cosinesimil",
                            "default_pipeline": pipeline_name,
                            "knn": "true"
                        }
                    }
                }
            )
        
        # Create roles
        role_definition = get_role_definition(tenant_config, tenant)
        execute_opensearch_operation(
            tenant_config[tenant]['domain'],
            "create_role",
            aws_auth,
            path_params={"role_name": f"{tenant}_role"},
            payload_updates=role_definition
        )
        
        # Create role mappings
        role_mapping = {"backend_roles": [tenant]}
        execute_opensearch_operation(
            tenant_config[tenant]['domain'],
            "create_role_mapping",
            aws_auth,
            path_params={"role_name": f"{tenant}_role"},
            payload_updates=role_mapping
        )
    except Exception as e:
        raise ValueError(f"Failed to setup OpenSearch for tenant {tenant}: {str(e)}")