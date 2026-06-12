from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .api import api_router
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting Quant AI Agent API (model: {settings.LLM_MODEL_NAME})")
    try:
        from .rag.qdrant_client import init_collection
        init_collection()
        print("Qdrant collection initialized")
    except Exception as e:
        print(f"Qdrant init skipped: {e}")
    yield
    print("Shutting down Quant AI Agent API")

app = FastAPI(title="Streak AI Quant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "detail": "Internal server error"})

@app.get("/")
def root():
    return {
        "message": "Quant AI Agent API is running",
        "model": settings.LLM_MODEL_NAME,
        "provider": settings.MARKET_DATA_PROVIDER
    }

@app.get("/health")
def health():
    return {"status": "ok"}
