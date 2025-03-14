from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
import json
import uuid

# Create a simple standalone app
app = FastAPI(
    title="Simple API",
    description="A simple API for testing",
)

# Configure CORS - allow all origins explicitly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return JSONResponse(content={
        "status": "ok",
        "message": "Simple API is running",
        "environment": os.getenv("VERCEL_ENV", "development"),
        "python_version": sys.version
    })

@app.get("/test")
async def test():
    """Test endpoint."""
    return JSONResponse(content={
        "status": "ok",
        "message": "Test endpoint is working correctly"
    })

@app.post("/chat")
async def chat(request: Request):
    """Simple chat endpoint that returns a mock response."""
    try:
        # Parse the request body
        body = await request.json()
        prompt = body.get("prompt", "")
        session_id = body.get("session_id") or str(uuid.uuid4())
        
        # Create a mock response
        return JSONResponse(content={
            "response": f"This is a mock response to: '{prompt}'",
            "session_id": session_id,
            "tool_calls": [],
            "request_id": f"req_{uuid.uuid4().hex[:10]}"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        ) 