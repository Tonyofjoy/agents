import json

def handler(request, response):
    # Set CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return response
    
    # Handle GET request for test
    if request.method == "GET":
        # Create response
        data = {
            "status": "ok",
            "message": "Test endpoint is working correctly"
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