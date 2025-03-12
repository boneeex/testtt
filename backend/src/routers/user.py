from fastapi import APIRouter
from typing import Annotated

from backend.src.utils import AuthActions


user_router = APIRouter(prefix="/users")


@user_router.get("/join_to_session")
async def join_to_session():
    ...


@user_router.get("/view_session_info")
async def view_session_info():
    ...



@user_router.post("/send_code")
async def send_code():
    ...


@user_router.post("/view_results")
async def view_results():
    ...