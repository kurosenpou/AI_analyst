"""
FastAPI main application entry point
Handles CORS, routing, and server startup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import upload, generate

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Business Agent MVP",
    description="Generate business reports from uploaded data using AI",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Business Agent MVP API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check with environment status"""
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
