from fastapi import APIRouter, Depends, HTTPException, status
from models.user_model import UserCreation, UserLogin
from Utils.OAuth import (
    get_current_user,
    authenticate_user_,
    create_access_token,
    get_current_active_manager,
    get_password_hash,
    check_password_match,
)
from database.database_connection import user_collection
import time
from Utils.Config import MANAGER_SECRET_KEY

routes = APIRouter()


@routes.post("/register-staff", response_description="Register user")
async def create_user(
    userPayload: UserCreation, manager: dict = Depends(get_current_active_manager)
):
    """
    Register a new staff user.

    This endpoint allows a manager to register a new staff member. The manager
    must be authenticated and the new user must not already exist. The endpoint
    will hash the password and ensure it matches the confirmation field before
    saving the user data.
    """
    if user_collection.find_one({"email": userPayload.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists."
        )
    if userPayload.role == "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot create a manager."
        )

    # Check password match
    check_password_match(userPayload.confirm_password, userPayload.password)
    user_data = userPayload.dict(exclude={"confirm_password"})
    user_data["password"] = get_password_hash(userPayload["password"])
    user_data["manager_id"] = str(manager.get("_id"))
    user_data["created_at"] = int(time.time())
    user_data["updated_at"] = int(time.time())

    # Insert user into collection
    result = await user_collection.insert_one(user_data)
    if result.inserted_id:
        return {
            "message": "User registered successfully",
            "user_id": str(result.inserted_id),
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Please try again."
    )


@routes.post("/login", response_description="Login to check details")
async def login_manager(userLoginPayload: UserLogin):
    """
    Authenticate a user and return an access token.

    This endpoint allows users to log in by providing their email and password.
    If the credentials are valid, it generates an access token for the user.
    """

    # Authenticate the user
    user = await authenticate_user_(userLoginPayload.email, userLoginPayload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect email or password"
        )

    # Prepare data for the access token
    data = {
        "email": user.get("email"),
        "role": user.get("role"),
        "_id": str(user.get("_id")),
    }
    access_token = create_access_token(data)
    if access_token:
        return {"access_token": access_token}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to generate access token. Please try again.",
    )


@routes.post("/register-manager", response_description="Register user")
async def create_user(userPayload: UserCreation):
    """
    Register a new manager user.

    This endpoint allows the registration of a manager. The manager must provide
    a valid secret key and their role must be "manager". The endpoint will hash
    the password and ensure it matches the confirmation field before saving the
    user data.
    """
    # Check if user already exists
    if user_collection.find_one({"email": userPayload.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists."
        )

    # Validate role and secret key
    if userPayload.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access. Only managers can register.",
        )
    if userPayload.manager_secret_key != MANAGER_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret key. Please provide the correct secret key.",
        )

    # Check password match
    # Prepare user payload
    user_data = userPayload.dict(exclude={"confirm_password"})
    user_data["password"] = get_password_hash(userPayload.password)
    user_data["created_at"] = int(time.time())
    user_data["updated_at"] = int(time.time())

    # Insert user into collection
    result = await user_collection.insert_one(user_data)
    if result.inserted_id:
        return {"message": "Manager registered successfully"}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Registration failed. Please try again.",
    )


@routes.get("/user", response_description="Get current user detail")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Retrieve the details of the currently authenticated user.

    This endpoint returns the information of the currently logged-in user, excluding
    sensitive fields such as the user ID.
    """
    if "_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User details not found."
        )

    # Remove the user ID from the response data
    user_info = {key: value for key, value in current_user.items() if key != "_id"}

    return user_info
