// Basic API handler for Vercel
export default function handler(req, res) {
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
      version: '1.0.0',
      timestamp: Date.now()
    });
  }
  
  // Handle POST request to chat endpoint
  if (req.method === 'POST' && req.url === '/api/chat') {
    const sessionId = req.body?.session_id || `session-${Math.random().toString(36).substring(2, 15)}`;
    const prompt = req.body?.prompt || '';
    
    // Generate a response based on the prompt
    let response;
    
    if (prompt.toLowerCase().includes('generate a') && prompt.toLowerCase().includes('about')) {
      response = generateTemplateContent(prompt);
    } else {
      response = generateResponse(prompt);
    }
    
    return res.status(200).json({
      response,
      session_id: sessionId,
      tool_calls: [],
      request_id: `req_${Math.random().toString(36).substring(2, 15)}`
    });
  }
  
  // Handle unknown routes
  return res.status(404).json({
    status: 'error',
    message: 'Endpoint not found'
  });
}

// Generate a template-based content
function generateTemplateContent(prompt) {
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

// Generate a response to a question
function generateResponse(prompt) {
  const responses = [
    `At Tony Tech Insights, we focus on making technology accessible for businesses of all sizes. ${prompt} is an important consideration for modern businesses.`,
    `Technology is transforming how businesses operate. When it comes to ${prompt}, companies should focus on strategic implementation that aligns with their core business objectives.`,
    `${prompt} represents a significant opportunity for businesses to gain competitive advantage. The key is to start with clear goals and measure results consistently.`,
    `From our experience at Tony Tech Insights, successful implementation of solutions related to ${prompt} requires both technical expertise and business acumen.`
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
} 