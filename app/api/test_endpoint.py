from fastapi import FastAPI, APIRouter

# Create a router for test endpoints
router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is working."""
    return {
        "status": "ok",
        "message": "Test endpoint is working correctly"
    }

# Function to include this router in the main app
def include_test_router(app: FastAPI):
    app.include_router(router, prefix="/api", tags=["test"]) 