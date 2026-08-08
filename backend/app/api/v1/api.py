from fastapi import APIRouter
from app.api.v1 import auth, users, chat, feedback, prompts, inference

# Central v1 router. Add new routers here as each week is completed.
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(feedback.router)
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(inference.router, prefix="/inference", tags=["inference"])
