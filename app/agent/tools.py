from typing import Dict, List, Optional, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Input for the web search tool."""
    query: str = Field(..., description="The search query to look up on the web")


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


class CodeGenerationInput(BaseModel):
    """Input for the code generation tool."""
    language: str = Field(..., description="The programming language to generate code in")
    task: str = Field(..., description="The programming task to generate code for")


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


# Dictionary of available tools
AVAILABLE_TOOLS = {
    "web_search": WebSearchTool(),
    "generate_code": CodeGenerationTool(),
} 