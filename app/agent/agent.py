import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
import json
from pydantic import BaseModel, Field

from langchain.agents import AgentExecutor, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.callbacks.manager import CallbackManager
from langchain.schema import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.tools import AVAILABLE_TOOLS
from app.deepseek.wrapper import DeepSeekWrapper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('agent')

# Dictionary to store active requests
ACTIVE_REQUESTS = {}


class AgentResponse(BaseModel):
    """Structured response from the agent."""
    
    response: str = Field(..., description="The agent's response to the user query")
    session_id: str = Field(..., description="The session ID for this conversation")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="List of tools called during processing")
    thoughts: Optional[str] = Field(None, description="The agent's reasoning process (if available)")
    request_id: Optional[str] = Field(None, description="Request ID for tracking and cancellation")


class DeepSeekAgent:
    """
    LangChain agent powered by DeepSeek API with tool support.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are a helpful AI content creation assistant for Tony Tech Insights, a company that provides affordable digital services to businesses of all sizes. 

Your primary goal is to create on-brand content that maintains a consistent voice, tone, and messaging that matches Tony Tech Insights' brand identity. Before creating content, check the content database for relevant examples to guide your response style.

Tony Tech Insights brand values:
- Innovation: Providing cutting-edge yet practical solutions
- Global Expertise: Applying international experience to local challenges
- Efficiency: Maximizing results while minimizing costs
- Reliability: Delivering dependable services and support
- Honesty: Transparent communication and trustworthy advice
- Respect: Treating every client with dignity and understanding

Tony Tech Insights' tone of voice is:
- Professional but not overly formal
- Knowledgeable without being condescending
- Clear and jargon-free when explaining technical concepts
- Honest and transparent about capabilities and limitations
- Approachable and friendly without being casual

When asked to create content:
1. Use the ContentDatabaseTool to find relevant examples of similar content
2. Follow the structure and style of these examples while customizing for the specific request
3. Ensure the content reflects Tony Tech Insights' affordable, accessible approach to technology
4. Include specific benefits and clear calls to action where appropriate
5. Maintain a consistent brand voice across all content types

If the user selects the "mai_phu_hung_brief" brand brief, switch to Vietnamese language mode and follow these additional guidelines:
- Communicate primarily in Vietnamese unless explicitly asked for English
- Use a friendly, enthusiastic tone appropriate for Vietnamese business communications
- Focus on the distribution of quality household and personal care products as the main business activity
- Incorporate the brand values: Natural ingredients, Eco-friendly production, Family safety, Vietnamese heritage, Quality and effectiveness
- Use the Mai Phú Hưng tone of voice: Friendly, Enthusiastic, Educational, Warm, and Family-oriented
- Emphasize the company's position as an exclusive distributor of quality household and personal care products
- Target the appropriate audience: Vietnamese families, health-conscious consumers, and environmentally-aware shoppers
- Use emojis and bullet points for better readability and engagement
- STRICTLY FOLLOW the content format specified in the brand brief, especially:
  - Use the exact post structure with emojis for social media content
  - Format product names in ALL CAPS with emoji accents
  - Always include the standard contact information block at the end of every post
  - Use the specified format for distributor information when appropriate
  - Incorporate the exact hashtag format from the brand brief
- When writing content for potential distributors, include the expanded contact information:
  👉 Liên hệ ngay để trở thành nhà phân phối & đại lý với giá thành tốt nhất:
  🏢 Công ty TNHH Mai Phú Hưng
  📞 Hotline: 0933.664.223 - 079.886.8886
  ☎️ CSKH: 0898.338.883 - 0778.800.900
  🌐 Website: maiphuhung.com
  📍 Địa chỉ: 31 Dân Tộc, P Tân Thành, Q Tân Phú, TP. Hồ Chí Minh
- Use the preferred hashtags and format them consistently
- Model all content after the example posts in the content database

Use other provided tools when appropriate to answer additional questions or gather information.
If you don't know the answer to a question, you can use the web_search tool to find information.
"""

    def __init__(
        self,
        deepseek_wrapper: DeepSeekWrapper,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        memory_window_size: int = 5,
    ):
        """
        Initialize the DeepSeek agent.
        
        Args:
            deepseek_wrapper: DeepSeek API wrapper
            tools: List of tools available to the agent
            system_prompt: Custom system prompt for the agent
            memory_window_size: Number of recent messages to keep in memory
        """
        self.deepseek_wrapper = deepseek_wrapper
        self.tools = tools or list(AVAILABLE_TOOLS.values())
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        # Set up memory for conversation history
        self.memory = ConversationBufferWindowMemory(
            k=memory_window_size,
            memory_key="chat_history",
            return_messages=True
        )
        
        # Prepare tool descriptions for the model
        self.tool_descriptions = self._prepare_tool_descriptions()
    
    def _prepare_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Prepare tool descriptions in the format DeepSeek API expects."""
        tool_descriptions = []
        
        for tool in self.tools:
            tool_desc = {
                "name": tool.name,
                "description": tool.description,
            }
            
            if hasattr(tool, "args_schema") and tool.args_schema is not None:
                schema = tool.args_schema.schema()
                properties = schema.get("properties", {})
                required = schema.get("required", [])
                
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": required
                }
                
                for prop_name, prop_info in properties.items():
                    parameters["properties"][prop_name] = {
                        "type": prop_info.get("type", "string"),
                        "description": prop_info.get("description", "")
                    }
                
                tool_desc["parameters"] = parameters
            
            tool_descriptions.append(tool_desc)
        
        return tool_descriptions
    
    async def _run_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Run a tool by name with arguments."""
        try:
            logger.info(f"Running tool '{tool_name}' with args: {json.dumps(tool_args)}")
            
            tool_found = False
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_found = True
                    try:
                        start_time = time.time()
                        
                        # Add timeout to avoid hanging
                        try:
                            result = await asyncio.wait_for(
                                tool.arun(**tool_args), 
                                timeout=20  # 20 second timeout for tools
                            )
                            
                            duration = time.time() - start_time
                            logger.info(f"Tool '{tool_name}' completed in {duration:.2f}s")
                            
                            return result
                        except asyncio.TimeoutError:
                            logger.error(f"Tool '{tool_name}' timed out after 20s")
                            return f"Error: Tool '{tool_name}' timed out. The agent will try to continue without using this tool."
                            
                    except Exception as e:
                        import traceback
                        error_message = f"Error executing tool '{tool_name}': {str(e)}\n{traceback.format_exc()}"
                        logger.error(error_message)
                        return f"Error: Tool '{tool_name}' failed with error: {str(e)}. The agent will continue processing your request."
            
            if not tool_found:
                logger.warning(f"Tool '{tool_name}' not found")
                return f"Error: Tool '{tool_name}' not found."
                
        except Exception as e:
            import traceback
            error_message = f"Unexpected error in _run_tool: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            return f"An unexpected error occurred when trying to run the tool: {str(e)}. The agent will continue processing your request."
    
    async def _process_function_calls(self, response: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Process function calls from DeepSeek API response."""
        try:
            function_call = self.deepseek_wrapper.extract_function_call(response)
            tool_calls = []
            
            if function_call:
                try:
                    tool_name = function_call.get("name", "")
                    arguments_str = function_call.get("arguments", "{}")
                    
                    logger.info(f"Request {request_id}: Tool call '{tool_name}'")
                    
                    # Handle potential JSON parsing errors
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError as e:
                        error_msg = f"Error parsing arguments JSON for tool '{tool_name}': {str(e)}"
                        logger.error(error_msg)
                        arguments = {}
                    
                    # Run the tool
                    tool_result = await self._run_tool(tool_name, arguments)
                    
                    # Record the tool call
                    tool_calls.append({
                        "tool": tool_name,
                        "args": arguments,
                        "result": tool_result
                    })
                    
                    # Check if we should continue with the tool result
                    if tool_result and not tool_result.startswith("Error:"):
                        # Add the tool result to messages and get a new response
                        tool_messages = [
                            {"role": "function", "name": tool_name, "content": tool_result}
                        ]
                        
                        # Get all the previous messages
                        previous_messages = response.get("choices", [{}])[0].get("message", {}).get("previous_messages", [])
                        
                        # Combine previous messages with function call result
                        new_messages = previous_messages + tool_messages
                        
                        # Get a new response from DeepSeek with function result included
                        try:
                            logger.info(f"Request {request_id}: Getting new response after tool call")
                            new_response = await self.deepseek_wrapper.generate_completion(
                                messages=new_messages,
                                functions=self.tool_descriptions,
                                use_cache=False,  # Don't cache agent responses with tool calls
                                request_id=request_id,
                                timeout=90,  # 90 second timeout for follow-up requests
                            )
                            
                            # Process any additional function calls recursively
                            result = await self._process_function_calls(new_response, request_id)
                            
                            # Combine tool calls
                            result["tool_calls"] = tool_calls + result.get("tool_calls", [])
                            
                            return result
                        except Exception as api_error:
                            logger.error(f"API error after tool call in request {request_id}: {str(api_error)}", exc_info=True)
                            # Return a response with just the tool result
                            text_response = self.deepseek_wrapper.extract_text_from_response(response)
                            return {
                                "response": f"{text_response}\n\nI encountered an error while processing the tool result. Here's what I found: {tool_result}",
                                "tool_calls": tool_calls
                            }
                    else:
                        # If there was an error with the tool, just continue with the original response
                        text_response = self.deepseek_wrapper.extract_text_from_response(response)
                        return {
                            "response": f"{text_response}\n\n{tool_result}",
                            "tool_calls": tool_calls
                        }
                    
                except Exception as e:
                    import traceback
                    error_msg = f"Error processing function call: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    
                    # If there's an error processing the function call, return the original response
                    # with the error message
                    text_response = self.deepseek_wrapper.extract_text_from_response(response)
                    return {
                        "response": f"{text_response}\n\nAn error occurred while processing a tool: {str(e)}. Let me continue without using the tool.",
                        "tool_calls": tool_calls
                    }
            
            # If no function call, just extract the text response
            text_response = self.deepseek_wrapper.extract_text_from_response(response)
            return {
                "response": text_response,
                "tool_calls": tool_calls
            }
        except Exception as e:
            import traceback
            error_msg = f"Unexpected error in _process_function_calls: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            # Return a fallback response in case of any unexpected exceptions
            try:
                # Try to extract at least the text response
                text_response = self.deepseek_wrapper.extract_text_from_response(response)
                return {
                    "response": f"{text_response}\n\nI encountered an unexpected error while processing your request. Let me try to continue our conversation without using additional tools.",
                    "tool_calls": []
                }
            except:
                # If even that fails, return a generic response
                return {
                    "response": "I encountered an unexpected error while processing your request. Please try again with a simpler query.",
                    "tool_calls": []
                }
    
    async def process_query(
        self, query: str, session_id: str
    ) -> AgentResponse:
        """
        Process a user query with the agent.
        
        Args:
            query: User's query
            session_id: Session identifier
            
        Returns:
            Structured agent response
        """
        # Generate a unique request ID for tracking
        request_id = f"req_{uuid.uuid4().hex[:10]}"
        logger.info(f"Processing query for session {session_id}, request {request_id}")
        
        try:
            # Register this request as active
            ACTIVE_REQUESTS[request_id] = {
                "session_id": session_id,
                "start_time": time.time(),
                "status": "processing",
                "agent": self,
            }
            
            # Get conversation history
            chat_history = self.memory.load_memory_variables({}).get("chat_history", [])
            
            # Prepare messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add chat history
            for message in chat_history:
                if isinstance(message, HumanMessage):
                    messages.append({"role": "user", "content": message.content})
                else:
                    messages.append({"role": "assistant", "content": message.content})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Start time for metrics
            start_time = time.time()
            
            logger.info(f"Request {request_id}: Sending to API with {len(messages)} messages")
            
            try:
                # Make API call with functions
                response = await self.deepseek_wrapper.generate_completion(
                    messages=messages,
                    functions=self.tool_descriptions,
                    temperature=0.7,
                    max_tokens=1024,
                    request_id=request_id,
                    timeout=120,  # Increased timeout to 120 seconds for initial request
                )
                
                logger.info(f"Request {request_id}: Received API response")
                
                # Process any function calls and get the final response
                processed_response = await self._process_function_calls(response, request_id)
                
                # Calculate response time
                response_time = time.time() - start_time
                logger.info(f"Request {request_id} completed in {response_time:.2f}s")
                
                # Update memory
                self.memory.save_context(
                    {"input": query},
                    {"output": processed_response["response"]}
                )
                
                # Update request status
                if request_id in ACTIVE_REQUESTS:
                    ACTIVE_REQUESTS[request_id]["status"] = "completed"
                
                # Return structured response
                return AgentResponse(
                    response=processed_response["response"],
                    session_id=session_id,
                    tool_calls=processed_response.get("tool_calls", []),
                    thoughts=None,  # DeepSeek doesn't expose reasoning steps
                    request_id=request_id
                )
            except Exception as api_error:
                logger.error(f"API error in request {request_id}: {str(api_error)}", exc_info=True)
                # Try to recover with a simpler response
                return AgentResponse(
                    response=f"I encountered an error while processing your request: {str(api_error)}. Please try a simpler query or try again later.",
                    session_id=session_id,
                    tool_calls=[],
                    thoughts=None,
                    request_id=request_id
                )
            
        except asyncio.CancelledError:
            logger.warning(f"Request {request_id} was cancelled")
            # Update request status
            if request_id in ACTIVE_REQUESTS:
                ACTIVE_REQUESTS[request_id]["status"] = "cancelled"
            return AgentResponse(
                response="I apologize, but your request was cancelled. Please try again.",
                session_id=session_id,
                tool_calls=[],
                thoughts=None,
                request_id=request_id
            )
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
            # Update request status
            if request_id in ACTIVE_REQUESTS:
                ACTIVE_REQUESTS[request_id]["status"] = "error"
                ACTIVE_REQUESTS[request_id]["error"] = str(e)
            return AgentResponse(
                response=f"I apologize, but I encountered an error while processing your request. Please try again with a simpler query.",
                session_id=session_id,
                tool_calls=[],
                thoughts=None,
                request_id=request_id
            )
            
        finally:
            # Clean up regardless of outcome
            if request_id in ACTIVE_REQUESTS:
                # Keep it for a while for status checks but mark as done
                if ACTIVE_REQUESTS[request_id].get("status") == "processing":
                    ACTIVE_REQUESTS[request_id]["status"] = "completed"
                # Schedule removal after 5 minutes to avoid memory leaks
                asyncio.create_task(self._delayed_request_cleanup(request_id, 300))

    async def _delayed_request_cleanup(self, request_id: str, delay_seconds: int):
        """
        Removes request data from memory after a delay.
        
        Args:
            request_id: The request ID to clean up
            delay_seconds: Number of seconds to wait before cleanup
        """
        try:
            await asyncio.sleep(delay_seconds)
            if request_id in ACTIVE_REQUESTS:
                del ACTIVE_REQUESTS[request_id]
                logger.debug(f"Cleaned up request {request_id} after {delay_seconds}s")
        except Exception as e:
            logger.error(f"Error cleaning up request {request_id}: {str(e)}")
            
    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel an ongoing request.
        
        Args:
            request_id: The request ID to cancel
            
        Returns:
            True if request was found and cancelled, False otherwise
        """
        if request_id in ACTIVE_REQUESTS:
            # Get the agent instance
            agent_data = ACTIVE_REQUESTS[request_id]
            if agent_data.get("status") == "processing":
                # Update status
                ACTIVE_REQUESTS[request_id]["status"] = "cancelling"
                
                # Cancel the request in the DeepSeek wrapper
                if hasattr(self.deepseek_wrapper, "cancel_request"):
                    self.deepseek_wrapper.cancel_request(request_id)
                    logger.info(f"Cancelled request {request_id}")
                    return True
                    
        return False

    @staticmethod
    def get_request_status(request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a request.
        
        Args:
            request_id: The request ID to check
            
        Returns:
            Status information or None if request not found
        """
        if request_id in ACTIVE_REQUESTS:
            status_data = ACTIVE_REQUESTS[request_id].copy()
            # Remove the agent reference to avoid serialization issues
            if "agent" in status_data:
                del status_data["agent"]
            return status_data
        return None 