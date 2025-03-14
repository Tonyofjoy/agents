"""
Tools available for the DeepSeek AI Agent.
"""

from typing import Dict, List, Type, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, Tool
import json

# Import tools
from app.agent.tools.brand_brief import BrandBriefTool
from app.agent.tools.content_generator import ContentGeneratorTool

class WebSearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="The search query to look up")


class CodeGenerationInput(BaseModel):
    """Input for code generation tool."""
    language: str = Field(description="Programming language to generate code in")
    task: str = Field(description="Description of what the code should do")


class WebSearchTool(BaseTool):
    """
    Tool for searching the web (mocked implementation).
    In a real implementation, this would connect to a search API.
    """
    name = "web_search"
    description = "Search the web for information about a specific query"
    args_schema = WebSearchInput

    def _run(self, query: str) -> str:
        """
        Mock implementation of web search.
        
        Args:
            query: The search query
            
        Returns:
            Mocked search results as a string
        """
        # Mock some responses based on keywords in the query
        query_lower = query.lower()
        
        if "weather" in query_lower:
            return "Today's weather is sunny with a high of 75°F and a low of 60°F."
        elif "news" in query_lower:
            return "Latest news: Scientists make breakthrough in AI research. Economy shows signs of growth."
        elif "python" in query_lower:
            return "Python is a high-level programming language known for its readability and versatility. The latest version is Python 3.11 with significant performance improvements."
        elif "deepseek" in query_lower:
            return "DeepSeek is an AI research company focused on developing advanced language models and AI systems."
        elif "langchain" in query_lower:
            return "LangChain is a framework for developing applications powered by language models, providing tools for chaining together LLM calls and integrating with external systems."
        else:
            return f"Search results for '{query}': Found multiple relevant resources. Consider refining your search."

    async def _arun(self, query: str) -> str:
        """Async implementation of web search."""
        return self._run(query)


class CodeGenerationTool(BaseTool):
    """Tool for generating code snippets."""
    name = "generate_code"
    description = "Generate code snippets in a specific programming language"
    args_schema = CodeGenerationInput

    def _run(self, language: str, task: str) -> str:
        """
        Generate code snippets (uses mock responses).
        
        Args:
            language: Programming language
            task: Description of the code to generate
            
        Returns:
            Code snippet as a string
        """
        language_lower = language.lower()
        
        if language_lower == "python":
            if "hello world" in task.lower():
                return "```python\nprint('Hello, World!')\n```"
            elif "file" in task.lower():
                return "```python\ndef read_file(filename):\n    with open(filename, 'r') as f:\n        return f.read()\n\ndef write_file(filename, content):\n    with open(filename, 'w') as f:\n        f.write(content)\n```"
            else:
                return "```python\n# Python code for: " + task + "\n# Implement your solution here\n```"
        elif language_lower == "javascript":
            if "hello world" in task.lower():
                return "```javascript\nconsole.log('Hello, World!');\n```"
            else:
                return "```javascript\n// JavaScript code for: " + task + "\n// Implement your solution here\n```"
        else:
            return f"Code generation for {language} is not supported yet."

    async def _arun(self, language: str, task: str) -> str:
        """Async implementation of code generation."""
        return self._run(language, task)


class ContentDatabaseInput(BaseModel):
    """Input for content database tool."""
    action: str = Field(
        description="Action to perform (search, get_by_id, get_by_keyword, get_random, get_all, get_stats)"
    )
    content_type: Optional[str] = Field(
        None, 
        description="Type of content to search (blog_posts, email_templates, social_posts, ad_copy, product_descriptions)"
    )
    query: Optional[str] = Field(
        None, 
        description="Search query or keyword to use"
    )
    content_id: Optional[str] = Field(
        None, 
        description="ID of a specific content item"
    )
    count: Optional[int] = Field(
        1, 
        description="Number of random items to return"
    )


def create_content_database_tool():
    """Create a ContentDatabaseTool instance."""
    try:
        from app.agent.tools.content_database_tool import ContentDatabaseTool
        tool_instance = ContentDatabaseTool()
        print("ContentDatabaseTool initialized successfully.")
        
        def _run_tool(action: str, content_type: Optional[str] = None, 
                     query: Optional[str] = None, content_id: Optional[str] = None, 
                     count: Optional[int] = 1) -> str:
            """Run the content database tool."""
            try:
                result = tool_instance.run(action, content_type, query, content_id, count)
                # Convert result to string for the agent
                return json.dumps(result, indent=2)
            except Exception as e:
                import traceback
                error_msg = f"Error running content_database tool: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                return json.dumps({"error": error_msg, "status": "failed"}, indent=2)
        
        # Create a Tool instance instead of using a BaseTool class
        return Tool(
            name="content_database",
            description="""Search and retrieve branded content examples to inform your responses.
Use this tool to find existing Tony Tech Insights content that matches user queries
and adapt it to provide consistent, on-brand responses.""",
            func=_run_tool,
        )
        
    except Exception as e:
        import traceback
        error_msg = f"Error initializing ContentDatabaseTool: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # Create a dummy tool
        def _dummy_tool(*args, **kwargs):
            return json.dumps({"error": error_msg, "status": "failed"}, indent=2)
        
        return Tool(
            name="content_database",
            description="Content database tool (currently unavailable)",
            func=_dummy_tool,
        )


# Dictionary of available tools
AVAILABLE_TOOLS = {
    "brand_brief": BrandBriefTool(),
    "content_generator": ContentGeneratorTool(),
    "web_search": WebSearchTool(),
    "generate_code": CodeGenerationTool(),
    "content_database": create_content_database_tool(),
} 