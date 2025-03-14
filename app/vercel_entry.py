import os
import sys

# Set the app directory as the current working directory
app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)

# Add the parent directory (agents) to the path to ensure correct imports
parent_dir = os.path.dirname(app_dir)
sys.path.insert(0, parent_dir)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(app_dir, '.env'))
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Import the FastAPI app
try:
    from app.api.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    raise

# Create the ASGI handler that Vercel expects
handler = app 