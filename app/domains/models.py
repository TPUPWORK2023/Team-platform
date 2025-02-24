from datetime import datetime
from typing import Dict, Any, List
from boto3.dynamodb.conditions import Key, Attr
from app.domains.config import create_dynamodb_resource
from decimal import Decimal
import uuid
import logging
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class TeamMemberDB:
    def __init__(self):
        """Initialize the TeamMemberDB class and set up the DynamoDB resource and table."""
        self.dynamodb = create_dynamodb_resource()
        self.table = self.dynamodb.Table('TeamMembers')

    async def create_team_member(self, team_member_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new team member in the DynamoDB table.

        Args:
            team_member_data (Dict[str, Any]): A dictionary containing team member details.

        Returns:
            Dict[str, Any]: The created team member item.
        """
        try:
            item = {
                'id': str(uuid.uuid4()),
                'manager_email': team_member_data['manager_email'],
                'team_member_email': team_member_data['email'],
                'status': team_member_data['status'],
                'invitedAt': datetime.now().isoformat(),
                'generation_link': team_member_data['generation_link'],
                'result_page_link': team_member_data['result_page_link'],
                'credits': team_member_data['credits'],
            }
            
            await run_in_threadpool(
                lambda: self.table.put_item(Item=item)
            )
            return item
        except Exception as e:
            raise Exception(f"Failed to create team member: {str(e)}")

    async def get_team_members(self, manager_email: str) -> List[Dict[str, Any]]:
        """Retrieve all team members associated with a specific manager.

        Args:
            manager_email (str): The email of the manager.

        Returns:
            List[Dict[str, Any]]: A list of team member items.
        """
        try:
            response = await run_in_threadpool(
                lambda: self.table.query(
                    IndexName='ManagerEmailIndex',
                    KeyConditionExpression=Key('manager_email').eq(manager_email)
                )
            )
            
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"DynamoDB query failed: {str(e)}")\
    
    async def update_credits_in_members(self, manager_email: str, team_member_email: str, new_credits: int) -> Dict[str, Any]:
        """
        Update the credits of a specific team member in the DynamoDB table.

        Args:
            manager_email (str): The email of the manager.
            team_member_email (str): The email of the team member whose credits should be updated.
            new_credits (int): The new credit value to set.

        Returns:
            Dict[str, Any]: The updated team member item.
        
        Raises:
            Exception: If the update operation fails.
        """
        try:
            # Fetch the team member's current record
            response = await run_in_threadpool(
                lambda: self.table.query(
                    IndexName='ManagerEmailIndex',  # Ensure this GSI exists!
                    KeyConditionExpression=Key('manager_email').eq(manager_email)
                )
            )
            
            items = response.get('Items', [])
            if not items:
                raise Exception(f"Team member not found: {team_member_email}")

            # Find the correct team member
            team_member = next((item for item in items if item["team_member_email"] == team_member_email), None)
            if not team_member:
                raise Exception(f"Team member not found: {team_member_email}")

            # Ensure credits do not go negative
            if new_credits < 0:
                raise Exception(f"Invalid credit value ({new_credits}) for {team_member_email}")

            # Perform the update operation in DynamoDB
            await run_in_threadpool(
                lambda: self.table.update_item(
                    Key={'id': team_member['id']},
                    UpdateExpression="SET credits = :new_credits",
                    ExpressionAttributeValues={":new_credits": new_credits},
                    ReturnValues="UPDATED_NEW"
                )
            )

            # Return the updated values
            team_member['credits'] = new_credits
            return team_member

        except Exception as e:
            raise Exception(f"Failed to update credits for {team_member_email}: {str(e)}")

    
    async def count_active_team_members(self, manager_email: str) -> int:
        """Count active (non-pending) team members under the given manager."""
        try:
            response = await run_in_threadpool(
                lambda: self.table.query(
                    IndexName='ManagerEmailIndex',  # Use GSI
                    KeyConditionExpression=Key('manager_email').eq(manager_email),
                    FilterExpression=Attr('status').ne('Pending')  # Correct usage
                )
            )
            return len(response['Items'])
        except Exception as e:
            logger.error(f"Error counting team members: {str(e)}")
            raise Exception(f"Error retrieving team size: {str(e)}")


class CreditsDB:
    def __init__(self):
        """Initialize the CreditsDB class and set up the DynamoDB resource and table."""
        self.dynamodb = create_dynamodb_resource()
        self.table = self.dynamodb.Table('Credits')

    async def get_credits(self, manager_email: str) -> int:
        """Get the number of credits for a specific manager.

        Args:
            manager_email (str): The email of the manager.

        Returns:
            int: The number of credits available for the manager.
        """
        try:
            # Perform the DynamoDB query
            response = self.table.query(
                IndexName='ManagerEmailIndex',
                KeyConditionExpression=Key('manager_email').eq(manager_email),
                ScanIndexForward=False,
                Limit=1
            )
            # Extract the credits from the response
            items = response.get('Items', [])
            if items:
                credits = items[0].get('credits', 0)
                # Convert Decimal to int if necessary
                return int(credits) if isinstance(credits, Decimal) else credits
            return 0  # Return 0 if no credits are found
        except Exception as e:
            logger.error(f"Error getting credits: {str(e)}")
            return 0

    async def create_credits(self, manager_email: str, credits: int) -> Dict[str, Any]:
        """Create a new credits record for a manager."""
        try:
            item = {
                "id": str(uuid.uuid4()),  # Generate a unique ID
                "manager_email": manager_email,
                "credits": credits,
                "last_updated": datetime.now().isoformat()
            }
            self.table.put_item(Item=item)
            return item
        except Exception as e:
            logger.error(f"Error creating credits record: {str(e)}")
            raise

    async def update_credits(self, manager_email: str, credits: int) -> Dict[str, Any]:
        """Update the existing credits record for a manager."""
        try:
            response = self.table.query(
                IndexName='ManagerEmailIndex',
                KeyConditionExpression=Key('manager_email').eq(manager_email),
                ScanIndexForward=False,
                Limit=1
            )
            items = response.get('Items', [])
            if items:
                id = items[0]['id']
                response = self.table.update_item(
                    Key={"id": id},
                    UpdateExpression="SET credits = :credits, last_updated = :last_updated",
                    ExpressionAttributeValues={
                        ":credits": credits,
                        ":last_updated": datetime.now().isoformat()
                    },
                    ReturnValues="ALL_NEW"
                )
                return response.get('Attributes', {})
            else:
                raise Exception("No existing record found to update.")
        except Exception as e:
            logger.error(f"Error updating credits for {manager_email}: {str(e)}")
            raise