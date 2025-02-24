import uuid
from pydantic import BaseModel
from datetime import datetime


class TeamMemberSchema(BaseModel):
    """Schema for a team member.

    Attributes:
        id (UUID): Unique identifier for the team member.
        email (str): The email of the team member.
        status (str): The status of the team member.
        invitedAt (datetime): The date and time when the team member was invited.
        generation_link (str): The link for generation.
        result_page_link (str): The link to the result page.
        manager_email (str): The email of the manager.
        credits (int, optional): The number of credits assigned to the team member.
    """
    id: uuid.UUID  # Ensure ID is properly typed as a UUID
    email: str
    status: str
    invitedAt: datetime
    generation_link: str
    result_page_link: str
    manager_email: str
    credits: int


class InviteRequestSchema(BaseModel):
    """Schema for inviting a new team member.

    Attributes:
        email (str): The email of the team member to be invited.
    """
    email: str


class InviteResponseSchema(BaseModel):
    """Schema for the response after inviting a team member.

    Attributes:
        status (str): The status of the invite request.
        email (str): The email of the invited team member.
    """
    status: str
    email: str


class ErrorResponseSchema(BaseModel):
    """Schema for error responses.

    Attributes:
        error (str): The error message.
    """
    error: str


class NotificationRequestSchema(BaseModel):
    """Schema for notification requests.

    Attributes:
        team_member_email (str): The email of the team member related to the notification.
        action (str): The action to be performed.
    """
    team_member_email: str
    action: str