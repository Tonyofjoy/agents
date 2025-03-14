"""
Content Database Utility Module.

This module provides a class to interact with the content database,
which stores sample content examples for the agent to reference.
"""

import os
import json
import random
from typing import Dict, List, Any, Optional, Union


class ContentDatabase:
    """
    A utility class to access the content database.
    
    This class provides methods to retrieve content types, search for content,
    and get content statistics.
    """
    
    def __init__(self, base_path=None):
        """
        Initialize the content database.
        
        Args:
            base_path (str, optional): The base path to the database directory.
                If not provided, it will be inferred based on this file's location.
        """
        # Try multiple possible paths to locate the database
        if base_path:
            self.base_path = base_path
        else:
            # Get the directory of this file
            file_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try current directory and alternatives
            possible_paths = [
                file_dir,  # Current directory
                os.path.join(os.path.dirname(file_dir), 'database'),  # ../database
                os.path.join(os.path.dirname(os.path.dirname(file_dir)), 'database'),  # ../../database
                os.path.join(os.getcwd(), 'app', 'database'),  # ./app/database from cwd
                os.path.join(os.getcwd(), 'database'),  # ./database from cwd
            ]
            
            # Find the first path that has db_index.json
            for path in possible_paths:
                index_path = os.path.join(path, 'db_index.json')
                if os.path.exists(index_path):
                    self.base_path = path
                    print(f"Found database at: {self.base_path}")
                    break
            else:
                # If not found, default to the current directory
                self.base_path = file_dir
                print(f"Database not found in any expected location, defaulting to: {self.base_path}")
        
        # Initialize cache
        self._db_index = None
        self._content_cache = {}
        
        # Try to load the database index
        try:
            self.load_db_index()
            print(f"Successfully loaded database index from {self.base_path}")
        except Exception as e:
            print(f"Error loading database index: {e}")
            # Create a minimal index if it doesn't exist
            self._db_index = {"content_types": [], "total_items": 0}
    
    def load_db_index(self) -> Dict[str, Any]:
        """
        Load the database index file.
        
        Returns:
            Dict[str, Any]: The database index as a dictionary.
        """
        index_path = os.path.join(self.base_path, 'db_index.json')
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Database index not found at {index_path}")
        
        with open(index_path, 'r', encoding='utf-8') as file:
            self._db_index = json.load(file)
        
        return self._db_index
    
    def _load_content_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load a content file.
        
        Args:
            file_path (str): The path to the content file.
            
        Returns:
            List[Dict[str, Any]]: The content items in the file.
        """
        # First try as an absolute path
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        
        # Then try relative to base_path
        rel_path = os.path.join(self.base_path, file_path)
        if os.path.exists(rel_path):
            with open(rel_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        
        # Finally try extracting just the filename and looking in the content directory
        filename = os.path.basename(file_path)
        content_path = os.path.join(self.base_path, 'content', filename)
        if os.path.exists(content_path):
            with open(content_path, 'r', encoding='utf-8') as file:
                return json.load(file)
                
        raise FileNotFoundError(f"Content file not found at {file_path} or {rel_path} or {content_path}")
    
    def get_content_types(self) -> List[str]:
        """
        Get a list of available content types.
        
        Returns:
            List[str]: A list of content type names.
        """
        if not self._db_index:
            self.load_db_index()
        
        return [item['type'] for item in self._db_index.get('content_types', [])]
    
    def get_all_content(self, content_type: str) -> List[Dict[str, Any]]:
        """
        Get all content items of a specific type.
        
        Args:
            content_type (str): The type of content to retrieve.
            
        Returns:
            List[Dict[str, Any]]: A list of content items.
        """
        if not self._db_index:
            self.load_db_index()
        
        # Check if the content type exists
        content_info = None
        for item in self._db_index.get('content_types', []):
            if item['type'] == content_type:
                content_info = item
                break
        
        if not content_info:
            return []
        
        # Check if content is already cached
        if content_type in self._content_cache:
            return self._content_cache[content_type]
        
        # Load content from file
        try:
            file_path = content_info['file_path']
            content = self._load_content_file(file_path)
            self._content_cache[content_type] = content
            return content
        except Exception as e:
            print(f"Error loading content for {content_type}: {e}")
            return []
        
    def get_content_by_id(self, content_type: str, content_id: str) -> Optional[Dict]:
        """Return a specific content item by ID."""
        content_items = self.get_all_content(content_type)
        for item in content_items:
            if item.get("id") == content_id:
                return item
        return None
        
    def get_content_by_keyword(self, content_type: str, keyword: str) -> List[Dict]:
        """Return content items that contain a specific keyword."""
        content_items = self.get_all_content(content_type)
        results = []
        
        for item in content_items:
            keywords = item.get("keywords", [])
            if keyword.lower() in [k.lower() for k in keywords]:
                results.append(item)
                
        return results
        
    def search_content(self, query: str, content_types: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Search across all content types for items matching the query.
        If content_types is provided, only search within those types.
        """
        if content_types is None:
            content_types = self.get_content_types()
            
        results = {}
        
        for content_type in content_types:
            content_items = self.get_all_content(content_type)
            matched_items = []
            
            for item in content_items:
                # Search in title
                if query.lower() in item.get("title", "").lower():
                    matched_items.append(item)
                    continue
                    
                # Search in content/description
                content_field = None
                if "content" in item:
                    content_field = item["content"]
                elif "full_description" in item:
                    content_field = item["full_description"]
                elif "description" in item:
                    content_field = item["description"]
                    
                if content_field and query.lower() in content_field.lower():
                    matched_items.append(item)
                    continue
                    
                # Search in keywords
                if any(query.lower() in keyword.lower() for keyword in item.get("keywords", [])):
                    matched_items.append(item)
                    
            if matched_items:
                results[content_type] = matched_items
                
        return results
        
    def get_random_content(self, content_type: str, count: int = 1) -> Union[Dict, List[Dict]]:
        """Return random content items of a specific type."""
        content_items = self.get_all_content(content_type)
        
        if not content_items:
            return [] if count > 1 else None
            
        if count == 1:
            return random.choice(content_items)
        else:
            # Get min(count, len(content_items)) random items
            count = min(count, len(content_items))
            return random.sample(content_items, count)
            
    def get_content_for_training(self, content_types: List[str] = None, max_per_type: int = None) -> Dict[str, List[Dict]]:
        """
        Get content for agent training, optionally limiting by content types and 
        maximum items per type. Returns a dictionary with content types as keys.
        """
        if content_types is None:
            content_types = self.get_content_types()
            
        training_data = {}
        
        for content_type in content_types:
            content_items = self.get_all_content(content_type)
            
            if max_per_type is not None and max_per_type < len(content_items):
                # Get a random sample if we're limiting the number per type
                content_items = random.sample(content_items, max_per_type)
                
            training_data[content_type] = content_items
            
        return training_data
        
    def get_content_statistics(self) -> Dict:
        """Return statistics about the content database."""
        stats = {
            "total_items": self._db_index.get("total_items", 0),
            "content_types": {}
        }
        
        for content_type in self.get_content_types():
            type_name = content_type
            content_items = self.get_all_content(type_name)
            
            stats["content_types"][type_name] = {
                "count": len(content_items),
                "description": self._db_index.get(f"{type_name}_description", "")
            }
            
        return stats

# Example usage
if __name__ == "__main__":
    db = ContentDatabase()
    print("Content Database Statistics:")
    print(json.dumps(db.get_content_statistics(), indent=2))
    
    # Example search
    print("\nSearch Results for 'cybersecurity':")
    results = db.search_content("cybersecurity")
    for content_type, items in results.items():
        print(f"\n{content_type}: {len(items)} results")
        for item in items:
            print(f"  - {item['title']}") 