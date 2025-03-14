import os
import sys
import uvicorn
from dotenv import load_dotenv

# Set the app directory as the current working directory
app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)

# Add the parent directory (agents) to the path to ensure correct imports
parent_dir = os.path.dirname(app_dir)
sys.path.insert(0, parent_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(app_dir, '.env'))

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting server at {host}:{port}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "app.api.main:app",  # Use absolute import path
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    ) 