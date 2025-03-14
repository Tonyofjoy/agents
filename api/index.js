// API handler for Vercel that connects to DeepSeek
import fetch from 'node-fetch';

// DeepSeek API configuration
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY; 
const DEEPSEEK_API_BASE = process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com/v1';

// Set timeouts - Vercel has a 10s limit for Hobby plans, but we'll set a buffer
const API_TIMEOUT = 8000; // 8 seconds total timeout
const API_BUFFER = 1000; // 1 second buffer for processing

// Define models for different scenarios to optimize performance
const FAST_MODEL = 'deepseek-chat';
const FALLBACK_MODEL = 'deepseek-chat';

// Fallback responses when DeepSeek is unavailable
const FALLBACK_RESPONSES = [
  "I understand your question about {topic}. As Tony Tech Insights, we specialize in making technology accessible for businesses. Could you provide more details so I can assist you better?",
  "That's an interesting question about {topic}. At Tony Tech Insights, we focus on practical tech advice for businesses. Let me know if you'd like more specific information.",
  "Thanks for asking about {topic}. This is an important area for businesses. I'd be happy to explore this further if you have specific questions.",
  "From a business technology perspective, {topic} offers several strategic opportunities. Would you like me to elaborate on any particular aspect?"
];

export default async function handler(req, res) {
  // Configure CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle OPTIONS request for CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Detailed logging for request debugging
  console.log(`[${new Date().toISOString()}] Received ${req.method} request to ${req.url}`);
  
  // Handle GET request to root endpoint (status check)
  if (req.method === 'GET') {
    const isDeepSeekConfigured = !!DEEPSEEK_API_KEY;
    
    return res.status(200).json({
      status: 'ok',
      message: 'Tony Tech Insights API is running',
      environment: process.env.VERCEL_ENV || 'development',
      deepseek_connected: isDeepSeekConfigured,
      deepseek_api_key_configured: isDeepSeekConfigured,
      version: '1.0.4',
      timestamp: Date.now()
    });
  }
  
  // Handle POST request to chat endpoint
  if (req.method === 'POST' && req.url.includes('/api/chat')) {
    let startTime = Date.now();
    try {
      // Parse body - handle both string and parsed JSON
      let body = req.body;
      if (typeof req.body === 'string') {
        try {
          body = JSON.parse(req.body);
        } catch (e) {
          console.error('[ERROR] Parsing request body:', e);
          return res.status(400).json({ error: 'Invalid JSON in request body' });
        }
      }
      
      // Generate IDs for session and request
      const sessionId = body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`;
      const requestId = `req_${Math.random().toString(36).substring(2, 15)}`;
      const prompt = body?.prompt || '';
      
      console.log(`[${requestId}] Processing request for session ${sessionId}`);
      console.log(`[${requestId}] Time elapsed: ${Date.now() - startTime}ms`);
      
      // Very quick response for empty prompts
      if (!prompt || prompt.length < 5) {
        console.log(`[${requestId}] Empty prompt detected, returning quick response`);
        return res.status(200).json({
          response: "I'd be happy to help! Please provide more details about what you'd like to discuss.",
          session_id: sessionId,
          request_id: requestId
        });
      }
      
      // Check for DeepSeek API key
      if (!DEEPSEEK_API_KEY) {
        console.error('[ERROR] DeepSeek API key not configured');
        return res.status(503).json({
          error: 'AI service unavailable - missing API key',
          session_id: sessionId,
          request_id: requestId
        });
      }
      
      // Create optimized system prompt - extremely short to reduce token usage
      const systemPrompt = "You're Tony Tech Insights' AI assistant. Provide concise, practical tech advice for businesses.";
      
      console.log(`[${requestId}] Calling DeepSeek API with timeout ${API_TIMEOUT}ms`);
      
      // Make the DeepSeek API call with strict timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        console.error(`[${requestId}] DeepSeek API call timed out after ${API_TIMEOUT}ms`);
      }, API_TIMEOUT);
      
      try {
        // Setup for a very lightweight API call
        const payload = {
          model: FAST_MODEL,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
          ],
          temperature: 0.7,
          max_tokens: 250, // Very limited token count for speed
          stream: false // Do not use streaming as it can be slower to init
        };
        
        console.log(`[${requestId}] DeepSeek API payload size: ${JSON.stringify(payload).length} bytes`);
        console.log(`[${requestId}] Time elapsed before API call: ${Date.now() - startTime}ms`);
        
        const apiCallStart = Date.now();
        const response = await fetch(`${DEEPSEEK_API_BASE}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
          timeout: API_TIMEOUT - API_BUFFER // Leave buffer for processing
        });
        
        const apiCallEnd = Date.now();
        console.log(`[${requestId}] DeepSeek API call completed in ${apiCallEnd - apiCallStart}ms`);
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`[${requestId}] DeepSeek API error (${response.status}): ${errorText}`);
          throw new Error(`DeepSeek API error: ${response.status} - ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`[${requestId}] Received DeepSeek response, parsing completed`);
        console.log(`[${requestId}] Total time elapsed: ${Date.now() - startTime}ms`);
        
        // Get the response content and return it
        const responseContent = data.choices[0].message.content;
        
        return res.status(200).json({
          response: responseContent,
          session_id: sessionId,
          request_id: requestId,
          elapsed_ms: Date.now() - startTime,
          tokens: data.usage?.total_tokens || 0
        });
        
      } catch (apiError) {
        clearTimeout(timeoutId);
        console.error(`[${requestId}] API call error: ${apiError.message}`);
        
        // Return proper error status instead of a fake success
        return res.status(503).json({
          error: `AI service error: ${apiError.message}`,
          session_id: sessionId,
          request_id: requestId
        });
      }
      
    } catch (error) {
      console.error(`[ERROR] Unhandled exception: ${error.stack || error.message}`);
      
      // Return error with appropriate status
      return res.status(500).json({
        error: `Server error: ${error.message}`,
        elapsed_ms: Date.now() - startTime
      });
    }
  }
  
  // Handle unknown routes
  return res.status(404).json({
    error: 'Endpoint not found',
    url: req.url,
    method: req.method
  });
}

// Generate a fallback response when DeepSeek is unavailable
function generateFallbackResponse(prompt) {
  const topic = prompt || 'your question';
  
  // Check for Vietnamese content
  const isVietnamese = 
    prompt.includes('tiếng Việt') || 
    prompt.includes('Vietnamese') ||
    /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(prompt);
  
  if (isVietnamese) {
    // Vietnamese fallback responses
    const responses = [
      `Tại Tony Tech Insights, chúng tôi tập trung vào việc giúp công nghệ dễ tiếp cận với các doanh nghiệp. Với câu hỏi về ${topic}, tôi có thể giúp gì thêm cho bạn?`,
      `Công nghệ đang thay đổi cách thức hoạt động của doanh nghiệp. Khi đề cập đến ${topic}, bạn có thể cung cấp thêm chi tiết để tôi có thể hỗ trợ tốt hơn không?`,
      `${topic} là một chủ đề quan trọng đối với doanh nghiệp. Tôi rất vui được trả lời bất kỳ câu hỏi cụ thể nào bạn có về vấn đề này.`,
      `Từ góc độ công nghệ kinh doanh, ${topic} mang lại nhiều cơ hội chiến lược. Bạn có muốn biết thêm về khía cạnh nào cụ thể không?`
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  } else {
    // Get a random response and replace {topic} with the actual topic
    const response = FALLBACK_RESPONSES[Math.floor(Math.random() * FALLBACK_RESPONSES.length)];
    return response.replace('{topic}', topic);
  }
} 