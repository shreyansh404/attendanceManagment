from fastapi import APIRouter, Depends, HTTPException, status
from models.shifts import Shifts
from Utils.OAuth import get_current_user
from database.database_connection import shift_collection, user_collection
from pymongo import ReturnDocument
from bson import ObjectId
import time

routes = APIRouter()

def validate_shift_times(shift_name: str, start_time: str, end_time: str):
    # Define the valid start and end times for each shift
    valid_times = {
        "morning": ("08:00", "16:00"),
        "afternoon": ("12:00", "21:00"),
        "evening": ("16:00", "03:00"),
        "night": ("21:00", "06:00")
    }

    # Convert shift_name to lowercase to ensure case-insensitive matching
    shift_name_lower = shift_name.lower()

    # Check if the shift_name is valid and if the start_time and end_time match the expected values
    if shift_name_lower in valid_times:
        expected_start_time, expected_end_time = valid_times[shift_name_lower]
        if start_time != expected_start_time or end_time != expected_end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{shift_name.capitalize()} shift should be from {expected_start_time} to {expected_end_time}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shift name"
        )
    
@routes.patch("", response_description="Shift register")
async def shift_register(
    shiftPayload: Shifts, 
    staff_id: str,  # The ID of the staff whose shift is being updated
    current_user: dict = Depends(get_current_user)
):
    """
    This function is used to register or update a shift for a staff member.
    Only a manager can perform this operation, and they can only change the shift of staff members they manage.
    """
    manager_id = str(current_user.get("_id"))

    # Check if the current user is a manager
    if current_user.get("role") != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers are allowed to change shifts"
        )
    print(staff_id)
    # Retrieve the staff member's data
    staff_member = user_collection.find_one({"_id": ObjectId(staff_id), "role": "staff"})

    if not staff_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    # Check if the manager is indeed the manager of this staff member
    if staff_member.get("manager_id") != manager_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to change this staff member's shift"
        )

    # Validate the shift times based on the shift name
    validate_shift_times(shiftPayload.shift_name, shiftPayload.start_time, shiftPayload.end_time)

    # Set the current time as the updated_at timestamp
    shiftPayload.updated_at = int(time.time())

    # Check if a shift for the staff member already exists
    existing_shift = shift_collection.find_one({"user_id": staff_id})

    if existing_shift:
        # Remove the '_id' field for comparison
        existing_shift.pop("_id", None)

        # If the new shift details are the same as the existing ones, return a conflict
        if shiftPayload.dict() == existing_shift:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Shift already exists"
            )
        shiftPayload = shiftPayload.dict()
        shiftPayload["user_id"] = staff_id
        # Update the existing shift with the new details
        updated_shift = shift_collection.find_one_and_update(
            {"user_id": staff_id},
            {"$set": shiftPayload},
            return_document=ReturnDocument.AFTER
        )
        updated_shift.pop("_id")
        if updated_shift:
            return {"msg": "Successfully updated shift", "shift": updated_shift}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update shift. Please try again."
            )
    else:
        # Set the current time as the created_at timestamp for a new shift
        shiftPayload.created_at = int(time.time())
        shiftPayload.user_id = staff_id

        # Insert the new shift
        shift_response = shift_collection.insert_one(shiftPayload.dict())
        if shift_response.inserted_id:
            return {"msg": "Successfully inserted shift", "shift_id": str(shift_response.inserted_id)}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to insert shift. Please try again."
            )
        
@routes.get("/", response_description="Current shift")
async def get_current_shift(current_user: dict = Depends(get_current_user)):
    """
        Retrieve the current shift details for the authenticated user.

        This endpoint fetches the shift information for the currently logged-in user
        based on their user ID. If no shift is found, a 404 error is returned.
    """
    user_id = str(current_user.get("_id"))
    
    existing_shift = shift_collection.find_one({"user_id": user_id})
    
    if not existing_shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No shift found.")
    
    existing_shift.pop("_id", None)
    
    return existing_shift