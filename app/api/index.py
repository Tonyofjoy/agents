import json
import os
import sys

def handler(request, response):
    # Set CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return response
    
    # Handle GET request for root
    if request.method == "GET":
        # Create response
        data = {
            "status": "ok",
            "message": "Simple API is running",
            "environment": os.getenv("VERCEL_ENV", "development"),
            "python_version": sys.version
        }
        
        # Send response
        response.status_code = 200
        response.content_type = "application/json"
        return response.send(json.dumps(data))
    
    # Method not allowed
    response.status_code = 405
    return response.send(json.dumps({
        "status": "error",
        "message": f"Method {request.method} not allowed"
    })) 