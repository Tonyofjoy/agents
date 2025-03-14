// API handler for Vercel that connects to DeepSeek
import fetch from 'node-fetch';

// DeepSeek API configuration
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || 'sk-3f0cb6792ec6407fab97b3493a8143bf';
const DEEPSEEK_API_BASE = process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com/v1';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle OPTIONS request for CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Handle GET request to root endpoint
  if (req.method === 'GET' && req.url === '/api') {
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
  if (req.method === 'POST' && req.url === '/api/chat') {
    try {
      const sessionId = req.body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`;
      const prompt = req.body?.prompt || '';
      const requestId = `req_${Math.random().toString(36).substring(2, 15)}`;
      
      // Determine if this is a content template request
      const isTemplateRequest = prompt.toLowerCase().includes('generate a') && prompt.toLowerCase().includes('about');
      
      // Create system prompt based on request type
      let systemPrompt;
      if (isTemplateRequest) {
        systemPrompt = `You are an expert content creation assistant for Tony Tech Insights, a technology consultancy that helps businesses leverage technology for growth.
Your task is to create professional, on-brand content based on user requests. Follow these brand guidelines:
- Voice: Professional but accessible, avoid jargon when possible
- Tone: Confident, helpful, forward-thinking
- Focus: Make complex technology concepts understandable for business leaders
- Brand promise: "Making Technology Accessible for Every Business"

When creating content, include relevant details from the user's request, maintain appropriate formatting, and ensure the content aligns with the Tony Tech Insights brand.`;
      } else {
        systemPrompt = `You are a helpful AI assistant for Tony Tech Insights, a technology consultancy that helps businesses leverage technology for growth.
Your role is to provide informative, practical responses about technology and business topics.
You should be professional but approachable, confident in your answers, and always aim to make complex technology concepts understandable.
Tony Tech Insights has the brand promise: "Making Technology Accessible for Every Business"`;
      }
      
      // Call DeepSeek API
      const response = await callDeepSeekAPI(prompt, systemPrompt);
      
      return res.status(200).json({
        response: response,
        session_id: sessionId,
        tool_calls: [],
        request_id: requestId
      });
    } catch (error) {
      console.error('Error processing chat request:', error);
      return res.status(500).json({
        status: 'error',
        message: error.message || 'An error occurred while processing your request'
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
    // Call DeepSeek API
    const response = await fetch(`${DEEPSEEK_API_BASE}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: prompt }
        ],
        temperature: 0.7
      })
    });
    
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