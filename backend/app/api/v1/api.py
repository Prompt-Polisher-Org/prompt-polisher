from fastapi import APIRouter
from app.api.v1 import auth, users

# Central v1 router. Add new routers here as each week is completed.
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
