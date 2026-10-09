from getpass import getpass
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from app.schemas import UserRole, CreateUser
from app.db import  SessionLocal
from app.services import create_new_user


def create_new_admin(create_admin_request: CreateUser)-> None:
    db = SessionLocal()
    try:
        create_new_user(db, create_admin_request, UserRole.ADMIN)
        db.commit()
        print(f"Admin '{create_admin_request.username}' created")
    except IntegrityError:
        db.rollback()
        print("Username or email already registered")
    finally:
        db.close()

if __name__ == "__main__":
    try:
        admin_request = CreateUser(
            username=input("Username: "), #3 - 20 characters
            email=input("Email: "), #valid email
            first_name=input("First name: "),
            last_name=input("Last name: "),
            password=getpass("Password: "),
            password_confirm=getpass("Confirm password: "),
            token="0123456789abcdef"
        )
    except ValidationError as e:
        print(e)
    else:
        create_new_admin(admin_request)