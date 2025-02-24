from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.team import get_team_members, invite_team_member, notify_manager
from app.schemas.team import TeamMemberSchema, InviteRequestSchema, InviteResponseSchema, NotificationRequestSchema
from app.dependencies.auth_dependencies import verify_token

router = APIRouter()

@router.post("/invite_team_member", response_model=InviteResponseSchema)
async def invite_team_member_route(
    invite_request: InviteRequestSchema, 
    manager: dict = Depends(verify_token)
) -> InviteResponseSchema:
    """Invite a new team member.

    Args:
        invite_request (InviteRequestSchema): The request containing the details of the team member to invite.
        manager (dict): The manager's information obtained from the token.

    Raises:
        HTTPException: If there is an error inviting the team member.

    Returns:
        InviteResponseSchema: The response containing the result of the invitation.
    """
    try:
        return await invite_team_member(invite_request, manager['email'])
    except HTTPException as e:
        raise e
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(
            status_code=status_code,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/get_team_members", response_model=List[TeamMemberSchema])
async def get_team_members_route(manager: dict = Depends(verify_token)) -> List[TeamMemberSchema]:
    """Retrieve the list of team members for the manager.

    Args:
        manager (dict): The manager's Team information obtained from the DB.

    Raises:
        HTTPException: If there is an error retrieving the team members.

    Returns:
        List[TeamMemberSchema]: A list of team members.    
    """
    try:
        team_members = await get_team_members(manager['email'])
        if not team_members:
            raise HTTPException(status_code=404, detail="No team members found")
        return team_members
    except HTTPException as e:
        raise e
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(
            status_code=status_code,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/send_notification")
async def send_notification(
    request: NotificationRequestSchema, 
    manager: dict = Depends(verify_token)
) -> dict:
    """Send a notification to a team member.

    Args:
        request (NotificationRequestSchema): The request containing the notification details.
        manager (dict): The manager's information obtained from the token.

    Raises:
        HTTPException: If there is an error sending the notification.

    Returns:
        dict: A dictionary containing the status of the notification.
    """
    try:
        if request.team_member_email == '' or request.action == '':
            raise HTTPException(status_code=400, detail=" Missing Team member email or action")
        await notify_manager(manager['email'], request.team_member_email, request.action)
        return {"status": "success", "message": "Notification sent"}
    except HTTPException as e:
        raise e
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        status_code = getattr(error, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=str(error))