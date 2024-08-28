from dotenv import load_dotenv
import os
from pathlib import Path  
import boto3  

env_path = Path('Utils/.env')
load_dotenv(dotenv_path=env_path)
database_url = os.getenv('DATABASE_URL')
user_collection_name = os.getenv("USER_COLLECTION")
attendance_collection_name = os.getenv("ATTENDANCE_COLLECTION")
database_name = os.getenv("DATABASE_NAME")
shift_collection_name = os.getenv("SHIFT_COLLECTION")
PRIVATE_KEY = os.getenv("PRIVATE_KEY").encode('utf-8')
PUBLIC_KEY = os.getenv("PUBLIC_KEY").encode('utf-8')
TOKEN_EXPIRE_TIME = int(os.getenv("TOKEN_EXPIRE_TIME"))
MANAGER_SECRET_KEY = os.getenv("MANAGER_SECRET_KEY")
AWS_ACCESS_KEY_ID= os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY= os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME=os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION=os.getenv("AWS_REGION")

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
bucket_name = AWS_S3_BUCKET_NAME    
