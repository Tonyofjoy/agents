import aiohttp
import json
import os
import time
import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union

from app.cache.redis import RedisClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('deepseek_wrapper')

class DeepSeekWrapper:
    """
    Wrapper class for the DeepSeek API with async methods and Redis caching.
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        redis_client: Optional[RedisClient] = None,
        cache_ttl: int = 3600,  # 1 hour cache by default
        request_timeout: int = 60,  # Default timeout in seconds
        mock_mode: bool = False,  # Enable mock mode for testing without API
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.request_timeout = request_timeout
        self.mock_mode = mock_mode or api_key.lower() in ("", "your_api_key_here", "none", "test")
        if self.mock_mode:
            logger.warning("DeepSeek wrapper running in MOCK MODE - no actual API calls will be made")
            
        # In-memory cache as fallback when Redis is not available
        self._memory_cache = {}
        # To store active requests for cancellation
        self._active_requests = {}

    async def _generate_cache_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """Generate a unique cache key for the request."""
        cache_data = {
            "messages": messages,
            "model": model,
        }
        return f"deepseek:{hash(json.dumps(cache_data, sort_keys=True))}"

    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        else:
            # Use in-memory cache if Redis is not available
            if cache_key in self._memory_cache:
                cache_entry = self._memory_cache[cache_key]
                # Check if cache entry is still valid
                if cache_entry["expires"] > time.time():
                    return cache_entry["data"]
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]
        return None

    async def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache the response with TTL."""
        if self.redis_client:
            await self.redis_client.set(
                cache_key, json.dumps(response), expire=self.cache_ttl
            )
        else:
            # Use in-memory cache if Redis is not available
            self._memory_cache[cache_key] = {
                "data": response,
                "expires": time.time() + self.cache_ttl
            }
            
            # Simple cache cleanup - remove oldest entries if cache gets too large
            if len(self._memory_cache) > 100:  # Arbitrary limit
                # Remove expired entries first
                now = time.time()
                expired_keys = [k for k, v in self._memory_cache.items() if v["expires"] <= now]
                for k in expired_keys:
                    del self._memory_cache[k]
                
                # If still too many entries, remove oldest
                if len(self._memory_cache) > 100:
                    oldest_key = min(self._memory_cache.keys(), key=lambda k: self._memory_cache[k]["expires"])
                    del self._memory_cache[oldest_key]

    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel an ongoing API request.
        
        Args:
            request_id: The ID of the request to cancel
            
        Returns:
            True if a request was found and cancelled, False otherwise
        """
        if request_id in self._active_requests:
            session, task = self._active_requests[request_id]
            if not task.done():
                logger.info(f"Cancelling request {request_id}")
                # Close the session which will abort any ongoing requests
                session.close()
                # Cancel the task
                task.cancel()
                # Remove from active requests
                del self._active_requests[request_id]
                return True
            else:
                # Task already completed, just remove from active requests
                del self._active_requests[request_id]
        return False

    async def _generate_mock_response(self, messages: List[Dict[str, str]], functions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate a mock response for testing without API access."""
        # Get the last user message
        last_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
        
        if not last_message:
            last_message = "Hello"
            
        # Generate a mock response
        await asyncio.sleep(1)  # Simulate API latency
        
        # Check if we should generate a function call
        if functions and "search" in last_message.lower():
            # Mock a web search function call
            search_function = None
            for func in functions:
                if func.get("name") == "web_search":
                    search_function = func
                    break
                    
            if search_function:
                return {
                    "id": f"mock-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "function_call": {
                                    "name": "web_search",
                                    "arguments": json.dumps({"search_term": last_message})
                                },
                                "previous_messages": messages
                            },
                            "finish_reason": "function_call"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150
                    }
                }
        
        # Return a basic text response
        return {
            "id": f"mock-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"This is a mock response from the DeepSeek API simulator. You asked: '{last_message}'. Since this is running in mock mode, I can't provide a real response. Please set a valid DEEPSEEK_API_KEY in your environment variables.",
                        "previous_messages": messages
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True,
        request_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a completion from DeepSeek API with caching support.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            functions: List of function definitions
            use_cache: Whether to use Redis caching
            request_id: Optional ID to track this request for cancellation
            timeout: Custom timeout for this request in seconds (overrides default)
            
        Returns:
            Response dictionary from DeepSeek API
        """
        # If in mock mode, return a mock response
        if self.mock_mode:
            logger.info(f"Using mock mode for request {request_id}")
            return await self._generate_mock_response(messages, functions)
        
        # Create a request ID if not provided
        if not request_id:
            request_id = f"req_{int(time.time() * 1000)}"
            
        # Use custom timeout if provided, otherwise use default
        request_timeout = timeout if timeout is not None else self.request_timeout
        
        # Check cache if enabled
        cache_key = None
        if use_cache:
            cache_key = await self._generate_cache_key(messages, self.model)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Cache hit for request {request_id}")
                return cached_response

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if functions:
            payload["functions"] = functions
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Track time for metrics
        start_time = time.time()
        session = None
        
        try:
            # Make API request
            session = aiohttp.ClientSession()
            
            # Create the task for the API request
            request_task = asyncio.create_task(
                self._make_api_request(
                    session,
                    f"{self.api_base}/chat/completions",
                    headers,
                    payload,
                    stream,
                    request_timeout,
                    cache_key,
                    use_cache,
                    request_id,
                )
            )
            
            # Store session and task for potential cancellation
            self._active_requests[request_id] = (session, request_task)
            
            # Wait for the task to complete
            result = await request_task
            
            # Log successful completion
            duration = time.time() - start_time
            logger.info(f"Request {request_id} completed in {duration:.2f}s")
            
            return result
            
        except asyncio.CancelledError:
            logger.warning(f"Request {request_id} was cancelled after {time.time() - start_time:.2f}s")
            # Clean up
            if session and not session.closed:
                await session.close()
            if request_id in self._active_requests:
                del self._active_requests[request_id]
            raise
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request {request_id} failed after {duration:.2f}s: {str(e)}")
            # Clean up
            if session and not session.closed:
                await session.close()
            if request_id in self._active_requests:
                del self._active_requests[request_id]
            raise
            
        finally:
            # Clean up regardless of outcome
            if request_id in self._active_requests:
                del self._active_requests[request_id]
            if session and not session.closed:
                await session.close()

    async def _make_api_request(
        self,
        session, 
        url, 
        headers, 
        payload, 
        stream, 
        timeout,
        cache_key,
        use_cache,
        request_id
    ):
        """Make the actual API request with timeout handling."""
        try:
            logger.info(f"Making API request for {request_id} (timeout: {timeout}s)")
            
            # Check if the request has been cancelled before making the API call
            if request_id not in self._active_requests:
                logger.warning(f"Request {request_id} was cancelled before API call")
                raise asyncio.CancelledError("Request cancelled before API call")
                
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error: {response.status} - {error_text} for request {request_id}")
                    
                    # Check for specific error types
                    if response.status == 429:
                        raise Exception(f"DeepSeek API rate limit exceeded. Please try again later.")
                    elif response.status == 401 or response.status == 403:
                        raise Exception(f"DeepSeek API authentication error. Please check your API key.")
                    elif response.status >= 500:
                        raise Exception(f"DeepSeek API server error ({response.status}). The service may be experiencing issues.")
                    else:
                        raise Exception(f"DeepSeek API error: {response.status} - {error_text}")
                
                if stream:
                    # Handle streaming response (return async generator)
                    return self._handle_streaming_response(response)
                else:
                    # Handle normal response
                    try:
                        # Use a timeout for reading the response as well
                        read_timeout = max(timeout / 2, 10)  # At least 10 seconds for reading
                        response_task = asyncio.create_task(response.json())
                        result = await asyncio.wait_for(response_task, timeout=read_timeout)
                        
                        # Cache result if caching is enabled
                        if use_cache and cache_key:
                            await self._cache_response(cache_key, result)
                        
                        return result
                    except asyncio.TimeoutError:
                        logger.error(f"Request {request_id} timed out while reading response after {read_timeout}s")
                        raise Exception(f"DeepSeek API response reading timed out after {read_timeout} seconds")
                    
        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out after {timeout}s")
            raise Exception(f"DeepSeek API request timed out after {timeout} seconds. Please try a simpler query or try again later.")
        except asyncio.CancelledError:
            logger.warning(f"Request {request_id} was cancelled during API call")
            raise
        except Exception as e:
            if str(e).startswith("DeepSeek API"):
                # Re-raise API-specific exceptions
                raise
            else:
                # Log and wrap other exceptions
                logger.error(f"Error during API request {request_id}: {str(e)}", exc_info=True)
                raise Exception(f"Error communicating with DeepSeek API: {str(e)}")

    async def _handle_streaming_response(self, response):
        """Handle streaming response from DeepSeek API."""
        buffer = ""
        async for line in response.content:
            if line:
                line_text = line.decode("utf-8").strip()
                if line_text.startswith("data: ") and line_text != "data: [DONE]":
                    json_str = line_text[6:]  # Remove "data: " prefix
                    try:
                        chunk = json.loads(json_str)
                        yield chunk
                    except json.JSONDecodeError:
                        pass

    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Extract text content from DeepSeek API response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def extract_function_call(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract function call from DeepSeek API response if present."""
        try:
            message = response["choices"][0]["message"]
            if "function_call" in message:
                return message["function_call"]
            return None
        except (KeyError, IndexError):
            return None
