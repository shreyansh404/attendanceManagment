from fastapi import FastAPI
from routes.authentication_routes import routes as auth
from routes.shift_routes import routes as shift
from routes.attendance_routes import router as attendance

app = FastAPI()


app.include_router(auth, prefix="/api/v1/auth")
app.include_router(shift, prefix="/api/v1/shift")
app.include_router(attendance, prefix="/api/v1/attendance")
