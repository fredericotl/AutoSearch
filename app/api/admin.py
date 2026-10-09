from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter
from starlette import status
from app.schemas import InviteResponse, CreateInvite
from app.db import get_db
from app.core import get_admin
from app.services.invite_service import create_invite

router = APIRouter(prefix="/admin", tags=["Admin"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_admin)]

@router.post("/invites", status_code=status.HTTP_201_CREATED, response_model=InviteResponse)
async  def create_new_invite(admin: admin_dependency, db: db_dependency, invite_request: CreateInvite):
    invite = create_invite(db, invite_request)
    db.commit()
    return invite