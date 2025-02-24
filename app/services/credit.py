from fastapi import HTTPException
from typing import List, Dict, Optional,Any
from app.schemas.team import TeamMemberSchema
from app.config import DISCOUNTS
from app.domains.models import CreditsDB, TeamMemberDB
import logging

logger = logging.getLogger(__name__)

async def load_team_members() -> List[TeamMemberSchema]:
    """Load team members from the database.

    Returns:
        List[TeamMemberSchema]: A list of team members.
    """
    team_db = TeamMemberDB()
    try:
        team_members = await team_db.get_all_team_members()
        return [TeamMemberSchema(**member) for member in team_members]
    except Exception as e:
        raise Exception(f"Error loading team members: {e}")

async def get_manager_team_size(manager_email: str) -> int:
    """Count active (non-pending) team members under the given manager.

    Args:
        manager_email (str): The email of the manager.

    Returns:
        int: The count of active team members.
    """
    team_db = TeamMemberDB()
    try:
        team_size = await team_db.count_active_team_members(manager_email)
        return team_size
    except Exception as e:
        raise Exception(f"Error counting team members: {e}")

def apply_discount(team_size: int) -> float:
    """
    Apply discount based on the number of active team members.

    Args:
        team_size (int): The size of the team.

    Returns:
        float: The discount rate (e.g., 0.10 for 10% discount).
    """
    # Find the applicable discount based on team size
    discount = next((rate for size, rate in DISCOUNTS if team_size >= size), 0)
    return discount

async def update_credit_data(manager_email: str, credits_purchased: int) -> Dict[str, Any]:
    """
    Update the credit data for a manager by adding the purchased credits.

    Args:
        manager_email (str): The email of the manager.
        credits_purchased (int): The number of credits purchased to add to the manager's total.

    Returns:
        Dict[str, Any]: The updated credits record for the manager.

    Raises:
        Exception: If an error occurs while fetching or updating the credits.
    """
    credits_db = CreditsDB()
    current_credits = await credits_db.get_credits(manager_email)
    new_total_credits = current_credits + credits_purchased

    if current_credits == 0:
        updated_credits = await credits_db.create_credits(manager_email, new_total_credits)
    else:
        updated_credits = await credits_db.update_credits(manager_email, new_total_credits)
    
    return updated_credits

async def get_credits(manager_email: str) -> int:
    """Get the number of credits for a specific manager.

    Args:
        manager_email (str): The email of the manager.

    Returns:
        int: The number of credits available for the manager.
    """
    credits_db = CreditsDB()
    try:
        # Perform the DynamoDB query
        credits = await credits_db.get_credits(manager_email)
        return credits
    except Exception as e:
        logger.error(f"Error getting credits: {str(e)}")
        return 0

async def invalidate_credit(team_member_email: str, manager_email: str) -> Dict[str, Optional[int]]:
    """Invalidate a credit from a team member and restore it to the manager's pool.

    Args:
        team_member_email (str): The email of the team member.
        manager_email (str): The email of the manager.

    Returns:
        Dict[str, Optional[int]]: A dictionary containing the status of the credit invalidation.
    
    Raises:
        Exception: If the team member or manager is not found or if the credit cannot be invalidated.
    """
    # Load team member data from DynamoDB
    team_db = TeamMemberDB()
    team_members = await team_db.get_team_members(manager_email)

    # Find the team member
    team_member = next((member for member in team_members if member['team_member_email'] == team_member_email), None)
    if not team_member:
        raise HTTPException(status_code=404, detail=f"Team member not found: {team_member_email}")

    # Check if the team member's status is "Pending" and has credits
    if team_member['status'] != "Pending":
        raise HTTPException(status_code=400, detail=f"Cannot invalidate credits for team member with status: {team_member['status']}")
    if team_member['credits'] < 1:
        raise HTTPException(status_code=404, detail=f"No credits found for team member: {team_member_email}")

    # Load manager's credits from DynamoDB
    credits_db = CreditsDB()
    current_credits = await credits_db.get_credits(manager_email)

    # Remove 1 credit from the team member
    team_member['credits'] -= 1

    # Restore 1 credit to the manager
    new_total_credits = current_credits + 1
    await credits_db.update_credits(manager_email, new_total_credits)

    # Update the team member data in DynamoDB
    await team_db.update_credits_in_members(
        manager_email,
        team_member["team_member_email"],
        team_member["credits"]
    )

    return {
        "status": "credit_invalidated",
        "email": team_member_email,
        "creditsRestored": 1,  
    }
