import os
import logging
from typing import Dict, List, Optional, Any, Union
import json
import uuid
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import glob
import time

from app.deepseek.wrapper import DeepSeekWrapper
from app.agent.agent import DeepSeekAgent, AgentResponse, ACTIVE_REQUESTS
from app.agent.tools import AVAILABLE_TOOLS
from app.cache.redis import RedisClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api")

app = FastAPI(
    title="DeepSeek AI Agent API",
    description="API for interacting with a DeepSeek-powered AI agent with tool capabilities",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Models for request/response
class ChatRequest(BaseModel):
    """Chat request model."""
    prompt: str = Field(..., description="User's prompt/query")
    session_id: Optional[str] = Field(None, description="Session ID (generated if not provided)")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID for this conversation")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools called during response generation")
    request_id: Optional[str] = Field(None, description="Request ID for tracking and cancellation")


class CancelRequest(BaseModel):
    """Request to cancel a processing request."""
    request_id: str = Field(..., description="ID of the request to cancel")


class CancelResponse(BaseModel):
    """Response to a cancellation request."""
    success: bool = Field(..., description="Whether the cancellation was successful")
    message: str = Field(..., description="Status message about the cancellation")


class RequestStatusResponse(BaseModel):
    """Response with status information about a request."""
    status: str = Field(..., description="Current status of the request (processing, completed, cancelled, error)")
    request_id: str = Field(..., description="ID of the request")
    session_id: str = Field(..., description="ID of the session")
    start_time: float = Field(..., description="Timestamp when the request started")
    elapsed_time: float = Field(..., description="Elapsed time in seconds since the request started")
    error: Optional[str] = Field(None, description="Error message if request failed")


# Dependency for getting Redis client
async def get_redis_client():
    """Get a Redis client as a dependency."""
    use_redis = os.getenv("USE_REDIS", "true").lower() == "true"
    
    if not use_redis:
        # Yield None if Redis is disabled
        yield None
        return
        
    try:
        redis_url = os.getenv("REDIS_URL")
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        client = RedisClient(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            url=redis_url,
        )
        
        # Test Redis connection
        await client.redis.ping()
        
        try:
            yield client
        finally:
            await client.close()
    except Exception as e:
        logger.warning(f"Redis connection error: {str(e)}. Proceeding without Redis.")
        yield None


# Dependency for getting DeepSeek agent
async def get_agent(redis_client: Optional[RedisClient] = Depends(get_redis_client)):
    """Get a DeepSeek agent as a dependency."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    # Check if API key is valid, otherwise use mock mode
    mock_mode = not api_key or api_key.lower() in ("", "your_api_key_here", "none", "test")
    if mock_mode:
        logger.warning("No valid DEEPSEEK_API_KEY found. Using mock mode.")
    
    # Initialize DeepSeek API wrapper
    deepseek_wrapper = DeepSeekWrapper(
        api_key=api_key,
        api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        redis_client=redis_client,
        cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
        mock_mode=mock_mode,
    )
    
    # Initialize agent with tools
    agent = DeepSeekAgent(
        deepseek_wrapper=deepseek_wrapper,
        tools=list(AVAILABLE_TOOLS.values()),
        system_prompt=os.getenv("AGENT_SYSTEM_PROMPT"),
        memory_window_size=int(os.getenv("MEMORY_WINDOW_SIZE", "5")),
    )
    
    return agent


@app.get("/")
async def root():
    """Root endpoint for health check."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    mock_mode = not api_key or api_key.lower() in ("", "your_api_key_here", "none", "test")
    
    return {
        "status": "ok", 
        "message": "DeepSeek Agent API is running", 
        "mock_mode": mock_mode
    }


@app.get("/brand-briefs")
async def list_brand_briefs():
    """List all JSON files in the tools directory that could be brand briefs."""
    tools_dir = os.path.join("app", "agent", "tools")
    # Make sure the directory exists
    if not os.path.exists(tools_dir):
        return {"briefs": []}
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(tools_dir, "*.json"))
    
    briefs = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                brief_data = json.load(f)
                # Only include files that might be brand briefs
                if "company_name" in brief_data:
                    filename = os.path.basename(file_path)
                    briefs.append({
                        "name": os.path.splitext(filename)[0],
                        "file_path": file_path,
                        "company_name": brief_data.get("company_name", "Unknown Company")
                    })
        except (json.JSONDecodeError, UnicodeDecodeError, IOError):
            # Skip files that aren't valid JSON or can't be read
            continue
    
    return {"briefs": briefs}


@app.get("/brand-briefs/{brief_name}")
async def get_brand_brief(brief_name: str):
    """Get a specific brand brief by name."""
    tools_dir = os.path.join("app", "agent", "tools")
    brief_path = os.path.join(tools_dir, f"{brief_name}.json")
    
    # Check if file exists
    if not os.path.exists(brief_path):
        raise HTTPException(status_code=404, detail=f"Brand brief '{brief_name}' not found")
    
    try:
        with open(brief_path, 'r', encoding='utf-8') as f:
            brief_data = json.load(f)
            return brief_data
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {brief_name}.json")
    except IOError:
        raise HTTPException(status_code=500, detail=f"Error reading file: {brief_name}.json")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: DeepSeekAgent = Depends(get_agent),
):
    """
    Chat with the DeepSeek agent.
    
    Args:
        request: Chat request with prompt and optional session_id
        agent: DeepSeek agent dependency
    
    Returns:
        Agent response
    """
    # Ensure we have a session ID
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Process the query with the agent
        agent_response = await agent.process_query(
            query=request.prompt,
            session_id=session_id,
        )
        
        # Return the response
        return {
            "response": agent_response.response,
            "session_id": session_id,
            "tool_calls": agent_response.tool_calls,
            "request_id": agent_response.request_id,
        }
        
    except Exception as e:
        # Log the error
        print(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/cancel", response_model=CancelResponse)
async def cancel_request(
    request: CancelRequest,
    agent: DeepSeekAgent = Depends(get_agent),
):
    """
    Cancel an ongoing request.
    
    Args:
        request: Cancellation request with request_id
        agent: DeepSeek agent dependency
    
    Returns:
        Cancellation status
    """
    request_id = request.request_id
    
    if not request_id:
        return CancelResponse(
            success=False,
            message="No request ID provided"
        )
    
    try:
        # Attempt to cancel the request
        success = agent.cancel_request(request_id)
        
        if success:
            logger.info(f"Request {request_id} cancelled successfully")
            return CancelResponse(
                success=True,
                message=f"Request {request_id} cancelled successfully"
            )
        else:
            logger.info(f"Request {request_id} could not be cancelled (not found or already completed)")
            return CancelResponse(
                success=False,
                message=f"Request {request_id} could not be cancelled (not found or already completed)"
            )
    except Exception as e:
        logger.error(f"Error cancelling request {request_id}: {str(e)}")
        return CancelResponse(
            success=False,
            message=f"Error cancelling request: {str(e)}"
        )


@app.get("/request-status/{request_id}", response_model=RequestStatusResponse)
async def get_request_status(
    request_id: str,
    agent: DeepSeekAgent = Depends(get_agent),
):
    """
    Get the status of a request.
    
    Args:
        request_id: ID of the request to check
        agent: DeepSeek agent dependency
    
    Returns:
        Status information about the request
    """
    if not request_id:
        raise HTTPException(status_code=400, detail="No request ID provided")
    
    # Get the status from the agent
    status_data = DeepSeekAgent.get_request_status(request_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Calculate elapsed time
    elapsed_time = time.time() - status_data.get("start_time", time.time())
    
    # Return the status
    return RequestStatusResponse(
        status=status_data.get("status", "unknown"),
        request_id=request_id,
        session_id=status_data.get("session_id", "unknown"),
        start_time=status_data.get("start_time", 0),
        elapsed_time=elapsed_time,
        error=status_data.get("error")
    ) 