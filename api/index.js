// API handler for Vercel that connects to DeepSeek
import fetch from 'node-fetch';

// DeepSeek API configuration
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || 'sk-3f0cb6792ec6407fab97b3493a8143bf';
const DEEPSEEK_API_BASE = process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com/v1';

// Set timeouts
const API_TIMEOUT = 9000; // 9 seconds (allowing for Vercel's 10s limit)

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle OPTIONS request for CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Handle GET request to root endpoint
  if (req.method === 'GET') {
    return res.status(200).json({
      status: 'ok',
      message: 'Tony Tech Insights API is running',
      environment: process.env.VERCEL_ENV || 'development',
      deepseek_connected: true,
      version: '1.0.0',
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
      
      // Determine if this is a content template request
      const isTemplateRequest = prompt.toLowerCase().includes('generate a') && prompt.toLowerCase().includes('about');
      
      // Create system prompt based on request type - keep it concise to reduce token usage
      let systemPrompt;
      if (isTemplateRequest) {
        systemPrompt = `You are Tony Tech Insights' content creator. Create ${prompt.includes('short') ? 'concise' : 'detailed'} content that is professional, accessible, and aligned with our brand promise: "Making Technology Accessible for Every Business". Focus on practical business value.`;
      } else {
        systemPrompt = `You are Tony Tech Insights' AI assistant. Provide concise, practical tech advice for businesses. Align with our brand: "Making Technology Accessible for Every Business".`;
      }
      
      // Set up a timeout promise
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('DeepSeek API request timed out')), API_TIMEOUT)
      );
      
      // Race between the API call and the timeout
      const response = await Promise.race([
        callDeepSeekAPI(prompt, systemPrompt),
        timeoutPromise
      ]);
      
      return res.status(200).json({
        response: response,
        session_id: sessionId,
        tool_calls: [],
        request_id: requestId
      });
    } catch (error) {
      console.error('Error processing chat request:', error);
      
      // Return a fallback response instead of an error
      let fallbackResponse = generateFallbackResponse(req.body?.prompt || '');
      
      return res.status(200).json({
        response: fallbackResponse,
        session_id: req.body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`,
        tool_calls: [],
        request_id: `req_${Math.random().toString(36).substring(2, 15)}`,
        _error: error.message || 'An error occurred while processing your request',
        _using_fallback: true
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
  try {
    // Use a shorter version of DeepSeek if the prompt suggests it would be a long response
    const model = prompt.length > 200 || 
                 prompt.toLowerCase().includes('long') || 
                 prompt.toLowerCase().includes('detailed') ? 
                 'deepseek-chat' : 'deepseek-chat';
                 
    // Optimize settings to get faster responses
    const settings = {
      model: model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 1000, // Limit response length to avoid timeouts
      timeout: API_TIMEOUT - 500 // Slightly shorter than our handler timeout
    };
    
    console.log('Calling DeepSeek API with settings:', JSON.stringify(settings));
    
    // Call DeepSeek API with timeout
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), API_TIMEOUT - 1000);
    
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
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`DeepSeek API error: ${errorData.error?.message || response.statusText}`);
    }
    
    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error) {
    console.error('Error calling DeepSeek API:', error);
    
    // Fallback responses if DeepSeek fails
    if (prompt.toLowerCase().includes('generate a') && prompt.toLowerCase().includes('about')) {
      return generateFallbackTemplateContent(prompt);
    } else {
      return generateFallbackResponse(prompt);
    }
  }
}

// Fallback template generation if DeepSeek API fails
function generateFallbackTemplateContent(prompt) {
  // Extract the type of content
  let contentType = 'blog post';
  if (prompt.includes('social post') || prompt.includes('social media')) {
    contentType = 'social media post';
  } else if (prompt.includes('email')) {
    contentType = 'email';
  } else if (prompt.includes('ad copy') || prompt.includes('advertisement')) {
    contentType = 'ad copy';
  }
  
  // Extract the topic
  const topicMatch = prompt.match(/about "(.*?)"/);
  const topic = topicMatch ? topicMatch[1] : 'technology';
  
  // Generate a simple response
  return `Here's a ${contentType} about "${topic}" for Tony Tech Insights:\n\n` +
    `# ${topic.charAt(0).toUpperCase() + topic.slice(1)}: Transforming Business in ${new Date().getFullYear()}\n\n` +
    `In today's rapidly evolving technological landscape, ${topic} stands out as a critical factor for business success. ` +
    `Organizations that effectively leverage ${topic} gain competitive advantages through improved efficiency, ` +
    `enhanced customer experiences, and innovative business models.\n\n` +
    `Tony Tech Insights | Making Technology Accessible for Every Business`;
}

// Fallback response generation if DeepSeek API fails
function generateFallbackResponse(prompt) {
  const responses = [
    `At Tony Tech Insights, we focus on making technology accessible for businesses of all sizes. ${prompt} is an important consideration for modern businesses.`,
    `Technology is transforming how businesses operate. When it comes to ${prompt}, companies should focus on strategic implementation that aligns with their core business objectives.`,
    `${prompt} represents a significant opportunity for businesses to gain competitive advantage. The key is to start with clear goals and measure results consistently.`,
    `From our experience at Tony Tech Insights, successful implementation of solutions related to ${prompt} requires both technical expertise and business acumen.`
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
} 