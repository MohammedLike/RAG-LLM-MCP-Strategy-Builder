from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import api_router

app = FastAPI(title="Streak AI Quant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Quant AI Agent API is running"}
