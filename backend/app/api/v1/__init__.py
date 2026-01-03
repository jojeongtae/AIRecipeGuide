"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import recipes

router = APIRouter()

router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])



