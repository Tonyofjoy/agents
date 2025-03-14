from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    """
    Test API endpoint handler.
    This endpoint provides a simple way to test that the API is functioning properly.
    """
    
    def do_GET(self):
        """Handle GET request to the test endpoint."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Test endpoint is working correctly"
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 