import json
import os
import sys
from typing import Dict, List, Any, Optional, Union

# More robust path handling
try:
    # Add the parent directory to the system path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    sys.path.append(parent_dir)
    
    # Try direct import first
    from database.db_utils import ContentDatabase
except ImportError:
    try:
        # Try with app prefix
        from app.database.db_utils import ContentDatabase
    except ImportError:
        # Fallback class if import fails
        class ContentDatabase:
            """Fallback content database class when imports fail."""
            
            def __init__(self, base_path=None):
                self.error_message = "Failed to import ContentDatabase. Path issues detected."
                
            def get_content_statistics(self):
                return {"error": self.error_message}
                
            def search_content(self, *args, **kwargs):
                return {"error": self.error_message}
                
            def get_random_content(self, *args, **kwargs):
                return None
                
            def get_content_by_id(self, *args, **kwargs):
                return None
                
            def get_content_by_keyword(self, *args, **kwargs):
                return []
                
            def get_all_content(self, *args, **kwargs):
                return []

class ContentDatabaseTool:
    """
    A tool for the agent to access the content database with branded content examples.
    This tool allows the agent to search, retrieve, and reference branded content for
    more consistent and accurate responses.
    """
    
    def __init__(self):
        """Initialize the content database tool."""
        try:
            self.db = ContentDatabase()
        except Exception as e:
            print(f"Error initializing ContentDatabase: {e}")
            self.db = ContentDatabase()  # Will use fallback if import failed
    
    @staticmethod
    def get_name() -> str:
        """Get the name of the tool."""
        return "ContentDatabaseTool"
    
    @staticmethod
    def get_description() -> str:
        """Get the description of the tool."""
        return (
            "Search and retrieve branded content examples from the database to inform "
            "your responses. Use this tool to find existing content that matches user queries "
            "and adapt it to provide consistent, on-brand responses."
        )
    
    @staticmethod
    def get_parameters() -> Dict:
        """Get the parameters schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "get_by_id", "get_by_keyword", "get_random", "get_all", "get_stats"],
                    "description": "The action to perform on the content database."
                },
                "content_type": {
                    "type": "string",
                    "description": "Type of content to query (blog_posts, email_templates, social_posts, ad_copy, product_descriptions)."
                },
                "query": {
                    "type": "string",
                    "description": "Search query or keyword to use (for search and get_by_keyword actions)."
                },
                "content_id": {
                    "type": "string",
                    "description": "ID of a specific content item (for get_by_id action)."
                },
                "count": {
                    "type": "integer",
                    "description": "Number of random items to return (for get_random action)."
                }
            },
            "required": ["action"]
        }
    
    def run(self, action: str, content_type: str = None, query: str = None, 
            content_id: str = None, count: int = 1) -> Dict:
        """
        Run the tool with the specified parameters.
        
        Args:
            action: The action to perform (search, get_by_id, get_by_keyword, get_random, get_all, get_stats)
            content_type: Type of content to query
            query: Search query or keyword
            content_id: ID of a specific content item
            count: Number of random items to return
            
        Returns:
            Dictionary with the action result
        """
        try:
            if action == "search":
                if not query:
                    return {"status": "error", "message": "Query parameter is required for search action"}
                
                # If content_type is provided, search only in that type
                content_types = [content_type] if content_type else None
                results = self.db.search_content(query, content_types)
                
                # Format the results for better readability
                formatted_results = {}
                for ctype, items in results.items():
                    formatted_results[ctype] = [self._format_item(item) for item in items]
                
                return {
                    "status": "success",
                    "action": action,
                    "query": query,
                    "results_count": sum(len(items) for items in results.values()),
                    "results": formatted_results
                }
                
            elif action == "get_by_id":
                if not content_type or not content_id:
                    return {"status": "error", "message": "Content type and content ID are required for get_by_id action"}
                
                item = self.db.get_content_by_id(content_type, content_id)
                if not item:
                    return {
                        "status": "error",
                        "message": f"Item with ID '{content_id}' not found in content type '{content_type}'"
                    }
                
                return {
                    "status": "success",
                    "action": action,
                    "content_type": content_type,
                    "content_id": content_id,
                    "item": self._format_item(item)
                }
                
            elif action == "get_by_keyword":
                if not content_type or not query:
                    return {"status": "error", "message": "Content type and query are required for get_by_keyword action"}
                
                items = self.db.get_content_by_keyword(content_type, query)
                
                return {
                    "status": "success",
                    "action": action,
                    "content_type": content_type,
                    "keyword": query,
                    "results_count": len(items),
                    "results": [self._format_item(item) for item in items]
                }
                
            elif action == "get_random":
                if not content_type:
                    return {"status": "error", "message": "Content type is required for get_random action"}
                
                items = self.db.get_random_content(content_type, count)
                if not items:
                    return {
                        "status": "error",
                        "message": f"No items found for content type '{content_type}'"
                    }
                
                # Handle both single item and list results
                if isinstance(items, list):
                    formatted_items = [self._format_item(item) for item in items]
                else:
                    formatted_items = self._format_item(items)
                
                return {
                    "status": "success",
                    "action": action,
                    "content_type": content_type,
                    "count": 1 if not isinstance(items, list) else len(items),
                    "results": formatted_items
                }
                
            elif action == "get_all":
                if not content_type:
                    return {"status": "error", "message": "Content type is required for get_all action"}
                
                items = self.db.get_all_content(content_type)
                
                return {
                    "status": "success",
                    "action": action,
                    "content_type": content_type,
                    "results_count": len(items),
                    "results": [self._format_item(item) for item in items]
                }
                
            elif action == "get_stats":
                stats = self.db.get_content_statistics()
                
                return {
                    "status": "success",
                    "action": action,
                    "statistics": stats
                }
                
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing {action}: {str(e)}"
            }
    
    def _format_item(self, item: Dict) -> Dict:
        """Format a content item for better readability in responses."""
        formatted = item.copy()
        
        # Make content more readable by replacing newlines with spaces for display
        if "content" in formatted:
            content = formatted["content"]
            # Preserve first 250 characters for preview, with newlines replaced by spaces
            preview = content[:250].replace("\n", " ")
            if len(content) > 250:
                preview += "..."
            formatted["content_preview"] = preview
            
        return formatted

if __name__ == "__main__":
    # Example usage for testing
    tool = ContentDatabaseTool()
    
    # Get statistics
    print("Database Statistics:")
    result = tool.run("get_stats")
    print(json.dumps(result, indent=2))
    
    # Search for content
    print("\nSearch for 'cybersecurity':")
    result = tool.run("search", query="cybersecurity")
    print(f"Found {result['results_count']} results")
    
    # Get random blog post
    print("\nRandom Blog Post:")
    result = tool.run("get_random", content_type="blog_posts")
    if result["status"] == "success":
        item = result["results"]
        print(f"Title: {item['title']}")
        print(f"Preview: {item.get('content_preview', '')}") 