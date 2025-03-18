import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
TABLE_NAME = os.environ['TABLE_NAME']

# AWS clients initialization
dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')

def extract_file_info(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract file information from S3 event record
    
    Args:
        record: S3 event record
        
    Returns:
        Dict: File information including bucket, key, size, tenant_id, unique_id
        
    Raises:
        ValueError: When record format is invalid
    """
    try:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']
        
        # Extract tenant ID and unique ID from the key (e.g., tenant-id/unique-id)
        parts = key.split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid key format: {key}")
            
        tenant_id = parts[0]
        unique_id = parts[1]
        
        return {
            'bucket': bucket,
            'key': key,
            'size': size,
            'tenant_id': tenant_id,
            'unique_id': unique_id
        }
    except (KeyError, IndexError) as e:
        raise ValueError(f"Invalid record format: {str(e)}")

def get_file_metadata(bucket: str, key: str) -> Dict[str, str]:
    """
    Get metadata from S3 object
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Dict: Object metadata
        
    Raises:
        Exception: When S3 operation fails
    """
    response = s3.head_object(Bucket=bucket, Key=key)
    return response.get('Metadata', {})

def register_document(file_info: Dict[str, Any], original_filename: str) -> None:
    """
    Register document in DynamoDB
    
    Args:
        file_info: File information
        original_filename: Original filename
        
    Raises:
        Exception: When DynamoDB operation fails
    """
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'pk': {'S': f'tenant#{file_info["tenant_id"]}'},
            'sk': {'S': f'documents#{file_info["unique_id"]}'},
            'fileName': {'S': original_filename},
            'fileSize': {'N': str(file_info["size"])},
            'bucket': {'S': file_info["bucket"]},
            'key': {'S': file_info["key"]},
            'uploadedAt': {'S': datetime.now().isoformat()},
            'status': {'S': 'not synced'},
            'uniqueId': {'S': file_info["unique_id"]}
        }
    )
    logger.info(f"Successfully registered document in DynamoDB: {file_info['unique_id']}")

def process_s3_record(record: Dict[str, Any]) -> None:
    """
    Process a single S3 event record
    
    Args:
        record: S3 event record
    """
    try:
        # Extract file information
        file_info = extract_file_info(record)
        logger.info(f"Processing file: {file_info['bucket']}/{file_info['key']}")
        
        # Get metadata from S3 object
        try:
            metadata = get_file_metadata(file_info['bucket'], file_info['key'])
            original_filename = metadata.get('original_filename', file_info['unique_id'])
        except Exception as e:
            logger.warning(f"Error getting S3 object metadata: {str(e)}")
            return
        
        # Register in DynamoDB
        try:
            register_document(file_info, original_filename)
        except Exception as e:
            logger.warning(f"Error registering document in DynamoDB: {str(e)}")
            
    except ValueError as e:
        logger.warning(f"Error processing record: {str(e)}")
    except Exception as e:
        logger.warning(f"Unexpected error processing record: {str(e)}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for tracking S3 file uploads
    
    Args:
        event: Lambda event containing S3 event records
        context: Lambda context
        
    Returns:
        Dict: Status response
    """
    records = event.get('Records', [])
    logger.info(f"Processing {len(records)} S3 events")
    
    for record in records:
        process_s3_record(record)
            
    return {"statusCode": 200, "body": "Processing complete"}