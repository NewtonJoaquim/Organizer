import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.services.file_service import file_service

logger = logging.getLogger("organizer.lgpd")


async def periodic_cleanup_worker() -> None:
    """
    Tarefa assíncrona periódica de contingência em background (RN-04 e RNF-03).
    Varre o disco a cada intervalo e expurga diretórios com tempo de vida superior ao TTL (15 minutos).
    """
    interval = settings.CLEANUP_WORKER_INTERVAL_SECONDS
    logger.info(
        f"[LGPD-TTL-WORKER] Worker de contingência iniciado "
        f"(intervalo: {interval}s, TTL: {settings.TEMP_FILE_TTL_MINUTES} min)."
    )
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                purged = file_service.purge_expired_files(settings.TEMP_FILE_TTL_MINUTES)
                if purged > 0:
                    logger.info(f"[LGPD-TTL-WORKER] {purged} diretórios expirados foram expurgados do disco.")
            except Exception as e:
                logger.error(f"[LGPD-TTL-WORKER] Erro durante purga periódica: {e}")
    except asyncio.CancelledError:
        logger.info("[LGPD-TTL-WORKER] Worker de contingência finalizado com sucesso.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = None
    if settings.ENABLE_CLEANUP_WORKER:
        worker_task = asyncio.create_task(periodic_cleanup_worker())
    try:
        yield
    finally:
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend REST API para o Organizer App - Organizador Inteligente de Dados e Planilhas. "
        "Permite ingestão multipart de planilhas (.xlsx e .xls) até 20 MB com integridade de dados."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configuração de CORS (RNF-06)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Registro de Rotas
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Organizer App API está em execução.",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
