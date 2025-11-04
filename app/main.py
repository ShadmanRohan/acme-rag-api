"""Main FastAPI application."""
from fastapi import FastAPI

app = FastAPI(title="Acme API", version="0.1.0")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

