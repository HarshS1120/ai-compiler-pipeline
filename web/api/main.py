"""FastAPI backend for the AI Compiler Pipeline"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.runner import PipelineRunner

# Initialize FastAPI
app = FastAPI(title="AI Compiler Pipeline", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline runner
runner = PipelineRunner()

class PromptRequest(BaseModel):
    prompt: str

class PipelineResponse(BaseModel):
    success: bool
    output: Optional[dict] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    return {
        "name": "AI Compiler Pipeline",
        "status": "running",
        "endpoints": {
            "generate": "/generate (POST)",
            "health": "/health (GET)"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate", response_model=PipelineResponse)
async def generate(request: PromptRequest):
    """Generate application configuration from natural language prompt"""
    
    prompt = request.prompt.strip()
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    if len(prompt) < 5:
        raise HTTPException(status_code=400, detail="Prompt too short")
    
    try:
        result = runner.run(prompt)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Serve static files from frontend
# Serve frontend at root
from fastapi.responses import FileResponse

@app.get("/app")
async def serve_frontend():
    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "frontend", 
        "index.html"
    )
    return FileResponse(frontend_path)

@app.get("/app/{path:path}")
async def serve_frontend_files(path: str):
    frontend_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "frontend"
    )
    file_path = os.path.join(frontend_dir, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}