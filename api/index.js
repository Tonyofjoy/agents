// API handler for Vercel that connects to DeepSeek
import fetch from 'node-fetch';

// DeepSeek API configuration
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || 'sk-3f0cb6792ec6407fab97b3493a8143bf';
const DEEPSEEK_API_BASE = process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com/v1';

// Set timeouts - increase to accommodate complex responses
const API_TIMEOUT = 25000; // 25 seconds (increased from 9 seconds)

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
    return res.status(200).json({
      status: 'ok',
      message: 'Tony Tech Insights API is running',
      environment: process.env.VERCEL_ENV || 'development',
      deepseek_connected: true,
      deepseek_api_key_length: DEEPSEEK_API_KEY ? DEEPSEEK_API_KEY.length : 0,
      version: '1.0.1',
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
      
      // Direct call to DeepSeek without timeout race
      try {
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
        
        // Generate fallback response based on the type of request
        let fallbackResponse;
        if (isTemplateRequest) {
          fallbackResponse = generateFallbackTemplateContent(prompt);
        } else {
          fallbackResponse = generateFallbackResponse(prompt);
        }
        
        return res.status(200).json({
          response: fallbackResponse,
          session_id: sessionId,
          tool_calls: [],
          request_id: requestId,
          using_deepseek: false,
          _error: deepseekError.message
        });
      }
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
  // Use a shorter version of DeepSeek if the prompt suggests it would be a long response
  const model = 'deepseek-chat';
  
  // Vietnamese content detection - optimize settings for Vietnamese
  const isVietnamese = 
    prompt.includes('tiếng Việt') || 
    prompt.includes('Vietnamese') ||
    /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(prompt);
  
  // Optimize settings to get better responses
  const settings = {
    model: model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt }
    ],
    temperature: 0.7,
    max_tokens: isVietnamese ? 2000 : 1500, // Larger limit for Vietnamese content
    timeout: API_TIMEOUT - 1000
  };
  
  console.log('Calling DeepSeek API with settings:', JSON.stringify(settings));
  
  // Call DeepSeek API with abortable controller
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), API_TIMEOUT - 2000);
  
  // Make multiple retry attempts
  let attempt = 0;
  const maxAttempts = 2;
  
  while (attempt < maxAttempts) {
    attempt++;
    console.log(`DeepSeek API call attempt ${attempt} of ${maxAttempts}`);
    
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
      
      // If we got here, we have a successful response
      return data.choices[0].message.content;
      
    } catch (error) {
      console.error(`DeepSeek API attempt ${attempt} failed:`, error);
      
      // If we've used all attempts, throw the error
      if (attempt >= maxAttempts) {
        throw error;
      }
      
      // Otherwise wait briefly and try again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  // This should never be reached due to the throw in the loop above
  throw new Error('All DeepSeek API attempts failed');
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
  
  // Check if Vietnamese content is requested
  const isVietnamese = 
    prompt.includes('tiếng Việt') || 
    prompt.includes('Vietnamese') ||
    prompt.endsWith('Vietnamese.') ||
    /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(prompt);
  
  if (isVietnamese) {
    // Vietnamese fallback response
    return `Đây là ${contentType} về "${topic}" cho Tony Tech Insights:\n\n` +
      `# ${topic.charAt(0).toUpperCase() + topic.slice(1)}: Chuyển đổi Kinh doanh trong năm ${new Date().getFullYear()}\n\n` +
      `Trong bối cảnh công nghệ phát triển nhanh chóng ngày nay, ${topic} nổi bật như một yếu tố quan trọng cho sự thành công trong kinh doanh. ` +
      `Các tổ chức tận dụng hiệu quả ${topic} đạt được lợi thế cạnh tranh thông qua cải thiện hiệu suất, ` +
      `nâng cao trải nghiệm khách hàng và các mô hình kinh doanh sáng tạo.\n\n` +
      `Tony Tech Insights | Giúp Công nghệ Tiếp cận với Mọi Doanh nghiệp`;
  } else {
    // English fallback response  
    return `Here's a ${contentType} about "${topic}" for Tony Tech Insights:\n\n` +
      `# ${topic.charAt(0).toUpperCase() + topic.slice(1)}: Transforming Business in ${new Date().getFullYear()}\n\n` +
      `In today's rapidly evolving technological landscape, ${topic} stands out as a critical factor for business success. ` +
      `Organizations that effectively leverage ${topic} gain competitive advantages through improved efficiency, ` +
      `enhanced customer experiences, and innovative business models.\n\n` +
      `Tony Tech Insights | Making Technology Accessible for Every Business`;
  }
}

// Fallback response generation if DeepSeek API fails
function generateFallbackResponse(prompt) {
  // Check if Vietnamese content is requested
  const isVietnamese = 
    prompt.includes('tiếng Việt') || 
    prompt.includes('Vietnamese') ||
    prompt.endsWith('Vietnamese.') ||
    /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/.test(prompt);
  
  if (isVietnamese) {
    // Vietnamese responses
    const responses = [
      `Tại Tony Tech Insights, chúng tôi tập trung vào việc giúp công nghệ dễ tiếp cận với các doanh nghiệp ở mọi quy mô. ${prompt} là một yếu tố quan trọng đối với các doanh nghiệp hiện đại.`,
      `Công nghệ đang thay đổi cách thức hoạt động của doanh nghiệp. Khi đề cập đến ${prompt}, các công ty nên tập trung vào việc triển khai chiến lược phù hợp với mục tiêu kinh doanh cốt lõi.`,
      `${prompt} thể hiện một cơ hội đáng kể cho doanh nghiệp để đạt được lợi thế cạnh tranh. Chìa khóa là bắt đầu với mục tiêu rõ ràng và đo lường kết quả một cách nhất quán.`,
      `Từ kinh nghiệm tại Tony Tech Insights, việc triển khai thành công các giải pháp liên quan đến ${prompt} đòi hỏi cả chuyên môn kỹ thuật và kinh doanh.`
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  } else {
    // English responses
    const responses = [
      `At Tony Tech Insights, we focus on making technology accessible for businesses of all sizes. ${prompt} is an important consideration for modern businesses.`,
      `Technology is transforming how businesses operate. When it comes to ${prompt}, companies should focus on strategic implementation that aligns with their core business objectives.`,
      `${prompt} represents a significant opportunity for businesses to gain competitive advantage. The key is to start with clear goals and measure results consistently.`,
      `From our experience at Tony Tech Insights, successful implementation of solutions related to ${prompt} requires both technical expertise and business acumen.`
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  }
} 