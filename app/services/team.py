import re
import os
import uuid
import datetime
from typing import List, Dict
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.services.credit import get_credits, update_credit_data
from app.schemas.team import TeamMemberSchema, InviteRequestSchema, InviteResponseSchema
from app.domains.models import TeamMemberDB
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class TeamServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TeamMemberAlreadyExistsError(TeamServiceError):
    def __init__(self, email: str):
        super().__init__(
            message=f"Team member with email {email} is already invited",
            status_code=409
        )

async def save_team_member(team_member: TeamMemberSchema) -> None:
    """Save a new team member to the database.

    Args:
        team_member (TeamMemberSchema): The team member to be saved.

    Raises:
        TeamServiceError: If there is an error saving the team member.
    """
    try:
        team_db = TeamMemberDB()
        await team_db.create_team_member(team_member.model_dump())
    except Exception as e:
        raise TeamServiceError(
            message=f"Failed to save team member: {str(e)}"
        )   

async def get_team_members(manager_email: str) -> List[TeamMemberSchema]:
    """Retrieve all team members associated with a specific manager.

    Args:
        manager_email (str): The email of the manager.

    Returns:
        List[TeamMemberSchema]: A list of team members.

    Raises:
        TeamServiceError: If there is an error retrieving the team members.
    """

    team_db = TeamMemberDB()
    team_members = await team_db.get_team_members(manager_email)
    if not team_members:
        return []
        
    return [
        TeamMemberSchema(
        id=member['id'],
        email=member['team_member_email'],
        status=member['status'],
        invitedAt=member['invitedAt'],
        generation_link=member['generation_link'],
        result_page_link=member['result_page_link'],
        manager_email=member['manager_email'],
        credits=member['credits']
    )
    for member in team_members
    ]

def is_team_member_already_invited(email: str, team_members: List[Dict], manager_email: str) -> bool:
    """Check if a team member is already invited by the same manager.

    Args:
        email (str): The email of the team member.
        team_members (List[Dict]): The list of team members represented as dictionaries.
        manager_email (str): The email of the manager.

    Returns:
        bool: True if the team member is already invited, False otherwise.
    """
    for member in team_members:
        if (
            member.email == email
            and member.status == "Pending"
            and member.manager_email == manager_email
        ):
            return True
    return False

def is_valid_email(email: str) -> bool:
    """Validate the format of an email address.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email format is valid, False otherwise.
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def send_mail(to_email: str, subject: str, body: str) -> None:
    """Send an email using SendGrid.

    Args:
        to_email (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body (HTML format).
    
    Raises:
        ValueError: If the recipient email address is not provided.
    """
    from_email = os.getenv("FROM_EMAIL")

    if not from_email:
        raise ValueError("Sender email address must be provided.")

    if not to_email:
        raise ValueError("Recipient email address must be provided.")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body
    )
    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

async def invite_team_member(invite_request: InviteRequestSchema, manager_email: str) -> InviteResponseSchema:
    """
    Invite a new team member by sending an invitation email with a unique coupon code.

    Args:
        invite_request (InviteRequestSchema): The request containing the email of the team member to be invited.
        manager_email (str): The email of the manager sending the invitation.

    Raises:
        TeamServiceError: If the email format is invalid or the manager tries to invite themselves.
        TeamMemberAlreadyExistsError: If the team member is already invited.
        HTTPException: If there is an error sending the invitation email or any unexpected error occurs.

    Returns:
        InviteResponseSchema: The response indicating the status of the invitation and the email of the invited team member.
    """
    try:
        if not is_valid_email(invite_request.email):
            raise TeamServiceError(
                message="Invalid email format",
                status_code=400
            )

        if invite_request.email == manager_email:
            raise TeamServiceError(
                message="Manager cannot invite themselves",
                status_code=400
            )

        # Load existing team members
        team_members = await get_team_members(manager_email)
        if is_team_member_already_invited(invite_request.email, team_members, manager_email):
            raise TeamMemberAlreadyExistsError(invite_request.email)

        # Generate a coupon (UUID)
        coupon = str(uuid.uuid4())

        try:
            # Send email with the coupon
            email_subject = "Your Coupon for AI SuitUp"
            email_body = f"<strong>Your coupon code is: {coupon}</strong>"
            send_mail(invite_request.email, email_subject, email_body)
        except Exception as e:
            raise TeamServiceError(
                message=f"Failed to send invitation email: {str(e)}",
                status_code=500
            )
        # Check current credits
        current_credits = await get_credits(manager_email)
 
        if current_credits < 1:
            raise HTTPException(status_code=400, detail="Not enough credits. Please buy credits first.")
        
        await update_credit_data(manager_email, -1)
        # Create new team member instance
        new_member = TeamMemberSchema(
            id = uuid.uuid4(),
            email=invite_request.email,
            status="Pending",
            invitedAt=datetime.datetime.now().isoformat(),
            generation_link=f"https://aisuitup.com/generate/{invite_request.email}",
            result_page_link=f"https://aisuitup.com/results/{invite_request.email}",
            manager_email=manager_email,
            credits=1
        )

        # Save the team member
        await save_team_member(new_member)

        return InviteResponseSchema(status="invited", email=invite_request.email)

    except TeamServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

async def notify_manager(manager_email: str, team_member_email: str, action: str) -> None:
    """Send a notification email to the manager when a team member completes an action.

    Args:
        manager_email (str): The manager's email address.
        team_member_email (str): The team member's email address.
        action (str): The action performed ("upload_completed" or "headshots_received").

    Raises:
        ValueError: If the action type is invalid.
        TeamServiceError: If the team member is not found for the manager.
    """
    # Load existing team members
    team_members = await get_team_members(manager_email)
    # Check if the team member exists
    if not any(member.email == team_member_email for member in team_members):
        raise TeamServiceError(
            message=f"Team member with email {team_member_email} not found for manager {manager_email}",
            status_code=404
        )

    if action == "upload_completed":
        subject = "Team Member Completed Upload"
        body = f"<p>Your team member <b>{team_member_email}</b> has successfully uploaded their picture.</p>"
    elif action == "headshots_received":
        subject = "AI-Generated Headshots Ready"
        body = f"<p>Your team member <b>{team_member_email}</b> has received their AI-generated headshots.</p>"
    else:
        raise ValueError("Invalid action type.")

    send_mail(manager_email, subject, body)
