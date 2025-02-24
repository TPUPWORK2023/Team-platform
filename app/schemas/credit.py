from pydantic import BaseModel

class CreditsRequestSchema(BaseModel):
    """Schema for requesting credits.

    Attributes:
        credits (int): The number of credits to request.
    """
    credits: int

class CreditsResponseSchema(BaseModel):
    """Schema for the response containing credits.

    Attributes:
        credits (int): The number of credits available.
    """
    credits: int

class InvalidateCreditRequestSchema(BaseModel):
    """Schema for invalidating a credit.

    Attributes:
        team_member_email (EmailStr): The email of the team member whose credit is to be invalidated.
    """
    team_member_email: str