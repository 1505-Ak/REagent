from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.core.config import get_settings
from app.api import chat, properties, preferences
from app.database.database import engine, Base

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="REAgent - AI Real Estate Concierge",
    description="An intelligent, autonomous real estate assistant",
    version="1.0.0"
)

# Settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])

@app.get("/")
async def root(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "REAgent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 