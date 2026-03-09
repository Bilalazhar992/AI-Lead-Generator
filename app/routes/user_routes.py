from fastapi import APIRouter, Request
from app.controllers.user_controller import UserController


router = APIRouter(prefix="/api/user", tags=["User"])
user_controller = UserController()




