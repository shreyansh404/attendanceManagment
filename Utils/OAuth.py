import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo import ReturnDocument
from fastapi import HTTPException, status
from database.database_connection import user_collection as users_collection
from Utils.Config import PRIVATE_KEY,PUBLIC_KEY,TOKEN_EXPIRE_TIME

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = TOKEN_EXPIRE_TIME

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password.

    This function uses the password context to check if the plain password,
    when hashed, matches the provided hashed password.
    """
    
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash the given plain text password.

    """
    return pwd_context.hash(password)

def check_password_match(password: str, confirmPassword: str):
    """
    Verify that the provided password and confirmation password match.

    This function checks if the given password matches the confirmation password.
    If they do not match, it raises an HTTP 400 Bad Request error.
    """
    if password != confirmPassword:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password doesn't match.")

def create_access_token(data: dict):
    """
    Create a JWT access token with an expiration time.

    This function generates a JWT token encoded with the provided data. The token will
    have an expiration time set to the current time plus a specified number of minutes.

    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieve the current user based on the provided JWT token.

    This function decodes the JWT token to extract the user's email and fetches
    the user document from the database. If the token is invalid or the user is not found,
    a 401 Unauthorized error is raised.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        print(payload)
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = users_collection.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_manager(current_user: dict = Depends(get_current_user)):
    """
    Ensure the current user is a manager.

    This dependency function checks if the currently authenticated user has the role of "manager".
    If the user is not a manager, it raises a 403 Forbidden error. If the user is a manager, it returns
    the user's information.
    """
    if current_user["role"] != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )
    return current_user

async def authenticate_user_(email: str, password: str):
    """
        Authenticate a user based on email and password.

        This function checks if a user exists with the given email and if the provided
        password matches the stored password. It returns the user document if authentication
        is successful; otherwise, it returns None.
    """
    user = users_collection.find_one({"email": email})
    print(user)
    if not user or not verify_password(password, user["password"]):
        return None
    return user