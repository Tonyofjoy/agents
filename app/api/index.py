from http.server import BaseHTTPRequestHandler
import json
import uuid
import logging
import sys
import os
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_api")

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")
    
    def do_OPTIONS(self):
        """Handle OPTIONS request - needed for CORS preflight"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET request"""
        logger.info(f"GET request to {self.path}")
        
        try:
            if self.path == "/" or self.path == "/api":
                # Root endpoint
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "ok",
                    "message": "Simple API is running",
                    "environment": os.getenv("VERCEL_ENV", "development"),
                    "python_version": sys.version
                }
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == "/test" or self.path == "/api/test":
                # Test endpoint
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "ok",
                    "message": "Test endpoint is working correctly"
                }
                self.wfile.write(json.dumps(response).encode())
                
            else:
                # Catch-all route
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "ok",
                    "message": f"Endpoint {self.path} not implemented yet",
                    "path": self.path,
                    "method": "GET"
                }
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error in GET handler: {str(e)}", exc_info=True)
            error_traceback = traceback.format_exc()
            
            self.send_response(500)
            self._set_cors_headers()
            self.end_headers()
            
            response = {
                "status": "error",
                "message": str(e),
                "traceback": error_traceback
            }
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST request"""
        logger.info(f"POST request to {self.path}")
        
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            body_str = body_bytes.decode('utf-8')
            logger.info(f"Request body: {body_str}")
            
            if self.path == "/chat" or self.path == "/api/chat":
                # Chat endpoint
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                
                # Parse request body
                try:
                    if body_str:
                        body = json.loads(body_str)
                        prompt = body.get("prompt", "")
                        session_id = body.get("session_id") or str(uuid.uuid4())
                    else:
                        prompt = "Empty request"
                        session_id = str(uuid.uuid4())
                        
                    logger.info(f"Prompt: {prompt}, Session ID: {session_id}")
                    
                    # Create response
                    response = {
                        "response": f"This is a simple response to: '{prompt}'",
                        "session_id": session_id,
                        "tool_calls": [],
                        "request_id": f"req_{uuid.uuid4().hex[:10]}"
                    }
                    
                    logger.info(f"Response: {response}")
                    self.wfile.write(json.dumps(response).encode())
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                    response = {
                        "status": "error",
                        "message": f"Invalid JSON: {str(e)}"
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
            else:
                # Catch-all route
                self.send_response(200)
                self._set_cors_headers()
                self.end_headers()
                
                response = {
                    "status": "ok",
                    "message": f"Endpoint {self.path} not implemented yet",
                    "path": self.path,
                    "method": "POST"
                }
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error in POST handler: {str(e)}", exc_info=True)
            error_traceback = traceback.format_exc()
            
            self.send_response(500)
            self._set_cors_headers()
            self.end_headers()
            
            response = {
                "status": "error",
                "message": str(e),
                "traceback": error_traceback
            }
            self.wfile.write(json.dumps(response).encode()) 