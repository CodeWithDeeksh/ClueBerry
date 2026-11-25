from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import documents, investigations

app = FastAPI(
    title="ClueBerry API",
    description="MCP-powered payment evidence investigation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(investigations.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ClueBerry",
        "version": "0.1.0",
        "mcp_server": "clueberry-evidence-server",
    }
