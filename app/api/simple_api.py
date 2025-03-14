from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
import json
import uuid
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_api")

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

@app.options("/{path:path}")
async def options_route(request: Request, path: str):
    """Handle OPTIONS requests for CORS preflight."""
    logger.info(f"OPTIONS request for path: {path}")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/")
async def root():
    """Root endpoint for health check."""
    logger.info("Root endpoint called")
    return JSONResponse(
        content={
            "status": "ok",
            "message": "Simple API is running",
            "environment": os.getenv("VERCEL_ENV", "development"),
            "python_version": sys.version
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.get("/test")
async def test():
    """Test endpoint."""
    logger.info("Test endpoint called")
    return JSONResponse(
        content={
            "status": "ok",
            "message": "Test endpoint is working correctly"
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.post("/chat")
async def chat(request: Request):
    """Simple chat endpoint that returns a mock response."""
    logger.info("Chat endpoint called")
    
    try:
        # Get the raw request body
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        logger.info(f"Request body: {body_str}")
        
        # Parse JSON
        if body_str:
            try:
                body = json.loads(body_str)
                prompt = body.get("prompt", "")
                session_id = body.get("session_id") or str(uuid.uuid4())
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": f"Invalid JSON: {str(e)}"
                    },
                    headers={"Access-Control-Allow-Origin": "*"}
                )
        else:
            prompt = "Empty request"
            session_id = str(uuid.uuid4())
        
        logger.info(f"Prompt: {prompt}, Session ID: {session_id}")
        
        # Create a mock response
        response = {
            "response": f"This is a mock response to: '{prompt}'",
            "session_id": session_id,
            "tool_calls": [],
            "request_id": f"req_{uuid.uuid4().hex[:10]}"
        }
        
        logger.info(f"Response: {response}")
        return JSONResponse(
            content=response,
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        error_traceback = traceback.format_exc()
        logger.error(f"Traceback: {error_traceback}")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "traceback": error_traceback
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )

# Add a fallback route for any other API requests
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path: str, request: Request):
    """Catch-all route for any other API requests."""
    logger.info(f"Catch-all route called for path: {path}")
    return JSONResponse(
        content={
            "status": "ok",
            "message": f"Endpoint /{path} not implemented yet",
            "path": path,
            "method": request.method
        },
        headers={"Access-Control-Allow-Origin": "*"}
    ) 