"""Endpoint di health check."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("")
async def root():
    """Root API: verifica che il backend risponda."""
    return {"message": "Hello from FastAPI"}


@router.get("/hello")
async def hello():
    """Health check esteso."""
    return {"message": "Hello from the backend!"}
