import json
import uuid

def handler(request, response):
    # Set CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return response
    
    # Handle POST request for chat
    if request.method == "POST":
        try:
            # Get request body
            body = request.json()
            prompt = body.get("prompt", "")
            session_id = body.get("session_id") or str(uuid.uuid4())
            
            # Create response
            data = {
                "response": f"This is a simple response to: '{prompt}'",
                "session_id": session_id,
                "tool_calls": [],
                "request_id": f"req_{uuid.uuid4().hex[:10]}"
            }
            
            # Send response
            response.status_code = 200
            response.content_type = "application/json"
            return response.send(json.dumps(data))
            
        except Exception as e:
            # Handle errors
            response.status_code = 500
            return response.send(json.dumps({
                "status": "error",
                "message": str(e)
            }))
    
    # Method not allowed
    response.status_code = 405
    return response.send(json.dumps({
        "status": "error",
        "message": f"Method {request.method} not allowed"
    })) 