from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from datetime import datetime, timedelta
import time
from Utils.OAuth import get_current_user
from Utils.Config import s3_client,bucket_name
from database.database_connection import shift_collection, attendance_collection
from models.attendance import Attendance
from botocore.exceptions import NoCredentialsError
from typing import Dict
import os

router = APIRouter()

@router.post("/", response_description="Mark attendance with image")
async def mark_attendance(
    image: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    This API marks the attendance of the current user and stores an image in S3.
    """
    user_id = str(current_user.get("_id"))

    # Find the shift for the current user
    shift = shift_collection.find_one({"user_id": user_id})

    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found.")

    shift_start_time_str = shift["start_time"]
    shift_end_time_str = shift["end_time"]

    # Convert shift start and end times to datetime objects for today
    now = datetime.now()
    shift_start_time = datetime.strptime(shift_start_time_str, "%H:%M").time()
    shift_end_time = datetime.strptime(shift_end_time_str, "%H:%M").time()
    
    shift_start = datetime.combine(now.date(), shift_start_time)
    shift_end = datetime.combine(now.date(), shift_end_time)

    # Adjust for next day if shift end is before start time (i.e., overnight shift)
    if shift_end < shift_start:
        shift_end += timedelta(days=1)

    # Check if the current time is within 1 hour of shift timings
    current_time = datetime.now()
    if not (shift_start - timedelta(hours=1) <= current_time <= shift_end + timedelta(hours=1)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Attendance can only be marked within 1 hour of your shift timings."
        )

    # Check if attendance has already been marked for the current shift period
    existing_attendance = attendance_collection.find_one({
        "user_id": user_id,
        "date": now.strftime("%Y-%m-%d"),
        "status": "Present"
    })

    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance for this shift has already been marked."
        )

    # Save the image file to S3
    try:
        file_key = f"attendance_images/{int(time.time())}_{image.filename}"
        s3_client.upload_fileobj(image.file, bucket_name, file_key,    ExtraArgs={'ACL': 'public-read'}
)
        file_url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_key}"
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credentials for S3 are not configured properly."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading the image: {str(e)}"
        )

    # Create attendance record
    attendance_record = Attendance(
        user_id=user_id,
        date=now.strftime("%Y-%m-%d"),
        time_in=now.strftime("%H:%M:%S"),
        image=file_url,
        status="Present",
        created_at=datetime.now(),
        update_at=datetime.now()
    )

    # Insert attendance record into the database
    attendance_response = attendance_collection.insert_one(attendance_record.dict())

    if attendance_response.inserted_id:
        return {"msg": "Attendance marked successfully", "attendance_id": str(attendance_response.inserted_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to mark attendance. Please try again."
        )