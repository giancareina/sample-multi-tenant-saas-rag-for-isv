import json
import os
from typing import Dict, Any

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration file"""
    try:
        # Check if file is in config directory first
        config_path = os.path.join('config', filename)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        # Check if filename already includes config directory
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        # Extract just the filename without path
        base_filename = os.path.basename(filename)
        config_path = os.path.join('config', base_filename)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        # Fall back to original path
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load configuration from {filename}: {str(e)}")

def get_tenant_config() -> Dict[str, Dict[str, str]]:
    """Get tenant configuration combined with environment variables"""
    try:
        # Try to load from config directory first
        config_path = os.path.join('config', 'tenant.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                base_config = json.load(f)
        else:
            with open('tenant_config.json', 'r', encoding='utf-8') as f:
                base_config = json.load(f)
        
        domain_mapping = {
            'A': os.environ['OPENSEARCH_DOMAIN_A'],
            'B': os.environ['OPENSEARCH_DOMAIN_B']
        }
        
        tenant_config = {}
        for tenant, config in base_config.items():
            tenant_config[tenant] = {
                'domain': domain_mapping[config['domain']],
                'index': config['index']
            }
            
        return tenant_config
        
    except Exception as e:
        raise ValueError(f"Failed to get tenant configuration: {str(e)}")

def validate_environment() -> None:
    """Check if required environment variables are set"""
    required_vars = [
        'OPENSEARCH_DOMAIN_A',
        'OPENSEARCH_DOMAIN_B',
        'COGNITO_USER_POOL_ID',
        'TABLE_NAME',
        'COGNITO_APP_CLIENT_ID',
        'BEDROCK_ACCESS_ROLE',
        'AWS_REGION'
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")