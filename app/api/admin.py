from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Path, HTTPException
from starlette import status
from app.schemas import InviteResponse, CreateInvite
from app.db import get_db
from app.core import get_admin, ProductNotFound
from app.services import create_invite,get_product,delete_product

router = APIRouter(prefix="/admin", tags=["Admin"])

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[dict, Depends(get_admin)]

@router.post("/invites", status_code=status.HTTP_201_CREATED, response_model=InviteResponse)
async  def create_new_invite(admin: admin_dependency, db: db_dependency, invite_request: CreateInvite):
    invite = create_invite(db, invite_request)
    db.commit()
    return invite

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(admin: admin_dependency, db: db_dependency, product_id : int =Path(gt=0)):
    try:
        product_model = get_product(db,product_id)
        delete_product(db, product_model)
        db.commit()
    except ProductNotFound as e:
        raise HTTPException(404, str(e))