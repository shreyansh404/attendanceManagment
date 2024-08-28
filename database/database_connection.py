from Utils.Config import database_name,database_url, user_collection_name, attendance_collection_name, shift_collection_name
from pymongo import MongoClient


database_connection = MongoClient(database_url)[database_name]

user_collection = database_connection.get_collection(user_collection_name)
attendance_collection = database_connection.get_collection(attendance_collection_name)
shift_collection = database_connection.get_collection(shift_collection_name)