from datetime import timedelta, datetime, timezone
from fastapi import Depends,HTTPException
from typing import Annotated
from starlette import status
from passlib.context import  CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import  jwt, JWTError
from app.core.config import settings


SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
EXPIRE_DELTA = timedelta(minutes=20)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated= "auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

def is_password_equal(password, hashed_password):
    return bcrypt_context.verify(password, hashed_password)

def hash_password(password):
    return bcrypt_context.hash(password)

def create_access_token(username: str, user_id: int, user_role: str ):
    encode = {"sub": username, "id": user_id, "role": user_role}
    expires = datetime.now(timezone.utc) + EXPIRE_DELTA
    encode["exp"] = expires
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

#TODO diferenciar erro de token expirado
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Authentication Failed")
        return {"username": username, "id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= "Authentication Failed")

