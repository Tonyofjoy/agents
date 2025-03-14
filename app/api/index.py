from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class handler(BaseHTTPRequestHandler):
    """
    API root endpoint handler.
    This endpoint returns basic information about the API and its environment.
    """
    
    def do_GET(self):
        """Handle GET request to the API root."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Tony Tech Insights API is running",
            "environment": os.getenv("VERCEL_ENV", "development"),
            "python_version": sys.version
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 