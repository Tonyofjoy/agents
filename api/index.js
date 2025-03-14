// API handler for Vercel that connects to DeepSeek
import fetch from 'node-fetch';

// DeepSeek API configuration
// IMPORTANT: This hardcoded key doesn't work - use environment variable instead
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY; 
const DEEPSEEK_API_BASE = process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com/v1';

// Set a reasonable timeout - Vercel has a 10s limit for Hobby plans
const API_TIMEOUT = 9500; // 9.5 seconds (just under Vercel's limit)

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
  
  // Log request information for debugging
  console.log(`Received ${req.method} request to ${req.url}`);
  
  // Handle GET request to root endpoint
  if (req.method === 'GET') {
    // Check if DeepSeek API is configured
    const isDeepSeekConfigured = !!DEEPSEEK_API_KEY;
    
    return res.status(200).json({
      status: 'ok',
      message: 'Tony Tech Insights API is running',
      environment: process.env.VERCEL_ENV || 'development',
      deepseek_connected: isDeepSeekConfigured,
      deepseek_api_key_configured: isDeepSeekConfigured,
      version: '1.0.3',
      timestamp: Date.now()
    });
  }
  
  // Handle POST request to chat endpoint
  if (req.method === 'POST' && req.url.includes('/api/chat')) {
    try {
      // Parse body - handle both string and parsed JSON
      let body = req.body;
      if (typeof req.body === 'string') {
        try {
          body = JSON.parse(req.body);
        } catch (e) {
          console.error('Error parsing request body:', e);
        }
      }
      
      // Log the received body for debugging
      console.log('Received request body:', JSON.stringify(body, null, 2));
      
      const sessionId = body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`;
      const prompt = body?.prompt || '';
      const requestId = `req_${Math.random().toString(36).substring(2, 15)}`;
      
      // Quick response for short prompts
      if (prompt.length < 5) {
        return res.status(200).json({
          response: "I'd be happy to help! Please provide more details about what you'd like to discuss or create.",
          session_id: sessionId,
          tool_calls: [],
          request_id: requestId
        });
      }
      
      // Check if DeepSeek API is configured
      if (!DEEPSEEK_API_KEY) {
        console.log('DeepSeek API key not configured. Using fallback response.');
        return res.status(200).json({
          response: generateFallbackResponse(prompt),
          session_id: sessionId,
          tool_calls: [],
          request_id: requestId,
          using_deepseek: false,
          error: "DeepSeek API key not configured"
        });
      }
      
      // Determine if this is a content template request
      const isTemplateRequest = prompt.toLowerCase().includes('generate a') && prompt.toLowerCase().includes('about');
      
      // Create system prompt based on request type - keep it concise to reduce token usage
      let systemPrompt;
      if (isTemplateRequest) {
        systemPrompt = `You are Tony Tech Insights' content creator. Create ${prompt.includes('short') ? 'concise' : 'detailed'} content that is professional, accessible, and aligned with our brand promise: "Making Technology Accessible for Every Business". Focus on practical business value.`;
      } else {
        systemPrompt = `You are Tony Tech Insights' AI assistant. Provide concise, practical tech advice for businesses. Align with our brand: "Making Technology Accessible for Every Business".`;
      }
      
      console.log('Starting API call to DeepSeek...');
      
      try {
        // Try to call DeepSeek with a shorter timeout than Vercel's limit
        const response = await callDeepSeekAPI(prompt, systemPrompt);
        console.log('API call completed successfully');
        
        return res.status(200).json({
          response: response,
          session_id: sessionId,
          tool_calls: [],
          request_id: requestId,
          using_deepseek: true
        });
      } catch (deepseekError) {
        console.error('DeepSeek API error:', deepseekError);
        
        // Use fallback response but still return 200 status
        return res.status(200).json({
          response: generateFallbackResponse(prompt),
          session_id: sessionId,
          tool_calls: [],
          request_id: requestId,
          using_deepseek: false,
          error: deepseekError.message
        });
      }
      
    } catch (error) {
      console.error('Error processing chat request:', error);
      
      // Always return 200 with a fallback response
      return res.status(200).json({
        response: generateFallbackResponse(req.body?.prompt || ''),
        session_id: req.body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`,
        tool_calls: [],
        request_id: `req_${Math.random().toString(36).substring(2, 15)}`,
        error: error.message || 'An error occurred while processing your request',
        using_deepseek: false
      });
    }
  }
  
  // Handle unknown routes
  return res.status(404).json({
    status: 'error',
    message: 'Endpoint not found'
  });
}

// Call DeepSeek API to generate a response
async function callDeepSeekAPI(prompt, systemPrompt) {
  if (!DEEPSEEK_API_KEY) {
    throw new Error('DeepSeek API key not configured');
  }
  
  // Vietnamese content detection - optimize settings for Vietnamese
  const isVietnamese = 
    prompt.includes('tiếng Việt') || 
    prompt.includes('Vietnamese') ||
    /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(prompt);
  
  // Optimize settings for fast responses
  const settings = {
    model: 'deepseek-chat',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt }
    ],
    temperature: 0.7,
    max_tokens: isVietnamese ? 800 : 500, // Shorter limits to ensure response within timeout
    timeout: API_TIMEOUT - 1000
  };
  
  console.log('Calling DeepSeek API with settings:', JSON.stringify(settings));
  
  // Call DeepSeek API with abortable controller
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), API_TIMEOUT - 2000);
  
  try {
    const response = await fetch(`${DEEPSEEK_API_BASE}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify(settings),
      signal: controller.signal
    });
    
    clearTimeout(id);
    
    // Log the raw response 
    console.log(`DeepSeek API response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`DeepSeek API error response: ${errorText}`);
      
      // Parse the error data if possible
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { error: { message: `Status ${response.status}: ${errorText}` } };
      }
      
      throw new Error(`DeepSeek API error: ${errorData.error?.message || response.statusText}`);
    }
    
    const data = await response.json();
    console.log('DeepSeek API response:', JSON.stringify(data, null, 2));
    
    return data.choices[0].message.content;
    
  } catch (error) {
    console.error(`DeepSeek API call failed:`, error);
    throw error;
  }
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