from fastapi import APIRouter
from app.api.endpoints import inspect, process, semantic, upload

api_router = APIRouter()

# Health check
@api_router.get("/health", tags=["Monitoramento"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "organizer-backend"}

# Inclusão dos endpoints
api_router.include_router(upload.router)
api_router.include_router(inspect.router)
api_router.include_router(semantic.router)
api_router.include_router(process.router)
