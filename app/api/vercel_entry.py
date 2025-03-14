import sys
import os

# Add the parent directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from app.api.main import app
    
    # Print debug information
    print("Successfully imported FastAPI app")
    
except Exception as e:
    print(f"Error importing app: {str(e)}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal app for debugging
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def debug_root():
        return {
            "status": "error",
            "message": "Error importing main app",
            "error": str(e),
            "python_path": sys.path,
            "current_dir": os.getcwd(),
            "files_in_app_dir": os.listdir(os.path.dirname(os.path.abspath(__file__)))
        }

# This file is used as an entry point for Vercel
# It simply imports and exposes the FastAPI app instance 