import boto3
import os
from typing import Any

def create_dynamodb_client() -> Any:
    """Create a DynamoDB client using AWS credentials."""
    return boto3.client(
        'dynamodb',
        aws_access_key_id=os.environ.get('DB_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('DB_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('DB_AWS_SESSION_TOKEN'),
        region_name=os.environ.get('DB_AWS_DEFAULT_REGION'),
    )

def create_dynamodb_resource() -> Any:
    """Create a DynamoDB resource using AWS credentials."""
    return boto3.resource(
        'dynamodb',
        aws_access_key_id=os.environ.get('DB_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('DB_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('DB_AWS_SESSION_TOKEN'),
        region_name=os.environ.get('DB_AWS_DEFAULT_REGION')
    )