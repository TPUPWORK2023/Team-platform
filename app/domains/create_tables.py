from app.domains.config import create_dynamodb_client
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def create_dynamodb_tables() -> None:
    """Create the necessary DynamoDB tables for the application if they don't exist."""
    dynamodb = create_dynamodb_client()
    
    tables = {
        'TeamMembers': {
            'KeySchema': [
                {'AttributeName': 'manager_email', 'KeyType': 'HASH'},
                {'AttributeName': 'team_member_email', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'manager_email', 'AttributeType': 'S'},
                {'AttributeName': 'team_member_email', 'AttributeType': 'S'}
            ]
        },
        'Credits': {
            'KeySchema': [
                {'AttributeName': 'manager_email', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'manager_email', 'AttributeType': 'S'}
            ]
        }
    }
    
    for table_name, table_config in tables.items():
        try:
            # Check if table exists
            dynamodb.describe_table(TableName=table_name)
            logger.info(f"Table {table_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                try:
                    logger.info(f"Creating table {table_name}...")
                    dynamodb.create_table(
                        TableName=table_name,
                        KeySchema=table_config['KeySchema'],
                        AttributeDefinitions=table_config['AttributeDefinitions'],
                        ProvisionedThroughput={
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    )
                    logger.info(f"Table {table_name} created successfully!")
                except Exception as create_error:
                    logger.error(f"Error creating table {table_name}: {str(create_error)}")
                    raise
            else:
                logger.error(f"Error checking table {table_name}: {str(e)}")
                raise

if __name__ == "__main__":
    create_dynamodb_tables()