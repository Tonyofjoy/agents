from http.server import BaseHTTPRequestHandler
import json
import uuid

class handler(BaseHTTPRequestHandler):
    """
    Chat API endpoint handler.
    This endpoint handles chat requests from the frontend and returns responses.
    """
    
    def do_POST(self):
        """Handle POST request to the chat endpoint."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # Parse JSON body
            if request_body:
                body = json.loads(request_body)
                prompt = body.get("prompt", "")
                session_id = body.get("session_id") or str(uuid.uuid4())
            else:
                prompt = "Empty request"
                session_id = str(uuid.uuid4())
                
            # Create response
            response = {
                "response": f"This is a simple response to: '{prompt}'",
                "session_id": session_id,
                "tool_calls": [],
                "request_id": f"req_{uuid.uuid4().hex[:10]}"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Handle errors
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 