from fastapi import APIRouter
from .auth import router as auth_router
from .matchmaking import router as match_router
from .GameManager import router as game_router

#Creamos un router grande
api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(match_router)
api_router.include_router(game_router)
