// Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin + '/api';
let sessionId = generateSessionId(); // Initialize session ID immediately
let isSending = false;
let currentLanguage = 'en'; // Default language
let currentRequestId = null; // Track the current request ID for cancellation
let requestTimeoutId = null; // To track the timeout for long-running requests
let isDeepSeekConnected = false; // Track if DeepSeek is connected

// Timeouts - carefully tuned for optimal experiences
const FETCH_TIMEOUT = 12000; // 12 seconds timeout for fetch requests
const USER_FEEDBACK_TIMEOUT = 3000; // 3 seconds before showing first feedback message
const LONG_WAIT_WARNING = 6000; // 6 seconds before showing serious wait warning

// API retry settings
const MAX_RETRIES = 1; // Maximum number of retries for failed API calls
const RETRY_DELAY = 1000; // Delay between retries (1 second)

// DOM Elements - Chat
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusElement = document.getElementById('status');
const toolContainer = document.getElementById('tool-container');
const toolCallsContainer = document.getElementById('tool-calls');

// DOM Elements - Tabs
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

// DOM Elements - Language
const languageButtons = document.querySelectorAll('.language-btn');
const langElements = document.querySelectorAll('.lang-content');

// DOM Elements - Content Templates
const templateCards = document.querySelectorAll('.template-card');
const templateForm = document.getElementById('template-form');
const templateFormTitle = document.getElementById('template-form-title');
const templateBriefSelect = document.getElementById('template-brief-name');
const templateTopic = document.getElementById('template-topic');
const templatePlatformField = document.getElementById('platform-field');
const templatePlatform = document.getElementById('template-platform');
const templateLength = document.getElementById('template-length');
const templateKeywords = document.getElementById('template-keywords');
const templateCta = document.getElementById('template-cta');
const generateContentButton = document.getElementById('generate-content-button');
const cancelTemplateButton = document.getElementById('cancel-template-button');

// Event Listeners - Core
document.addEventListener('DOMContentLoaded', initApp);
userInput.addEventListener('keydown', handleKeyDown);
sendButton.addEventListener('click', sendMessage);

// Event Listeners - Tabs
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');
        switchTab(tabName);
    });
});

// Event Listeners - Language
languageButtons.forEach(button => {
    button.addEventListener('click', () => {
        const lang = button.getAttribute('data-lang');
        switchLanguage(lang);
    });
});

// Event Listeners - Content Templates
templateCards.forEach(card => {
    card.addEventListener('click', () => {
        const templateType = card.getAttribute('data-template');
        showTemplateForm(templateType);
    });
});
generateContentButton.addEventListener('click', generateContent);
cancelTemplateButton.addEventListener('click', hideTemplateForm);

// Functions - Core

async function initApp() {
    // Connect to API and check its status
    await initChat();
    
    // Set initial language
    switchLanguage(currentLanguage);
}

async function initChat() {
    try {
        console.log("Connecting to API at:", API_URL);
        
        // Show connecting status
        statusElement.textContent = 'Connecting...';
        statusElement.classList.remove('connected', 'disconnected');
        statusElement.classList.add('connecting');
        
        // Test connection to API with retry logic
        const response = await fetchWithRetry(`${API_URL}`, {
            method: 'GET',
            timeout: 5000 // Short timeout for initial connection
        });
        
        console.log("API response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`API returned status ${response.status}`);
        }
        
        const data = await response.json();
        console.log("API response data:", data);
        
        if (data.status === 'ok') {
            statusElement.textContent = 'Connected';
            statusElement.classList.add('connected');
            statusElement.classList.remove('disconnected', 'connecting');
            
            // Check if DeepSeek is connected
            isDeepSeekConnected = data.deepseek_connected === true;
            
            if (!isDeepSeekConnected) {
                console.warn("DeepSeek API is not configured.");
                addMessage('system', `Note: Our AI service is currently experiencing high demand. Responses may take longer than usual. Thank you for your patience.`);
            }
            
            // Session ID is already initialized at the top
            console.log('Using session ID:', sessionId);
        } else {
            throw new Error('API not responding correctly');
        }
    } catch (error) {
        console.error('Error connecting to API:', error);
        statusElement.textContent = 'Disconnected';
        statusElement.classList.remove('connected', 'connecting');
        statusElement.classList.add('disconnected');
        
        addMessage('system', `Error connecting to our AI service. Please refresh the page or try again later.`);
    }
}

// Helper function for API calls with automatic retry
async function fetchWithRetry(url, options = {}, retries = MAX_RETRIES) {
    const { timeout = FETCH_TIMEOUT } = options;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        }).finally(() => clearTimeout(timeoutId));
        
        return response;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error(`Fetch timeout after ${timeout}ms:`, url);
            throw new Error(`Request timed out after ${timeout}ms`);
        }
        
        if (retries > 0) {
            console.log(`Retrying fetch (${retries} attempts left)...`);
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            return fetchWithRetry(url, options, retries - 1);
        }
        
        throw error;
    }
}

function generateSessionId() {
    return 'session-' + Math.random().toString(36).substring(2, 15);
}

function handleKeyDown(event) {
    // Send message on Enter key (without Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Language Functions
function switchLanguage(lang) {
    // Update current language
    currentLanguage = lang;
    
    // Update language buttons
    languageButtons.forEach(btn => {
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update all translatable elements
    langElements.forEach(element => {
        updateElementLanguage(element);
    });
    
    // Update placeholders for inputs
    if (lang === 'en') {
        templateTopic.placeholder = "Main topic of the content";
        templateKeywords.placeholder = "keyword1, keyword2, ...";
        templateCta.placeholder = "e.g., Sign up, Learn more, etc.";
        userInput.placeholder = "Type your message here...";
    } else if (lang === 'vi') {
        templateTopic.placeholder = "Chủ đề chính của nội dung";
        templateKeywords.placeholder = "từ khóa1, từ khóa2, ...";
        templateCta.placeholder = "Ví dụ: Đăng ký, Tìm hiểu thêm, v.v.";
        userInput.placeholder = "Nhập tin nhắn của bạn ở đây...";
    }
}

// Helper function for applying language to a specific element
function updateElementLanguage(element) {
    const langContent = element.querySelector('.lang-content');
    if (langContent) {
        const translation = langContent.getAttribute(`data-lang-${currentLanguage}`);
        if (translation) {
            langContent.textContent = translation;
        }
    }
}

async function sendMessage() {
    // Do nothing if already sending a message
    if (isSending) {
        return;
    }
    
    const messageText = userInput.value.trim();
    if (!messageText) {
        return;
    }
    
    // Clear input and disable UI
    userInput.value = '';
    isSending = true;
    sendButton.disabled = true;
    
    // Add user message to chat
    addMessage('user', messageText);
    
    // Add typing indicator
    const typingMessage = addTypingIndicator();
    
    // Add cancel button
    const cancelButton = addCancelButton();
    cancelButton.addEventListener('click', handleRequestCancel);
    
    // Set up request timeout monitoring with appropriate timeouts
    setupRequestTimeout();
    
    try {
        console.log("Sending message to API:", messageText);
        
        // Ensure session ID is set
        if (!sessionId) {
            sessionId = generateSessionId();
        }
        
        // Prepare request payload
        const payload = {
            prompt: messageText,
            session_id: sessionId
        };
        
        // Send request to API with retry capability
        const response = await fetchWithRetry(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
            timeout: FETCH_TIMEOUT
        });
        
        // Remove typing indicator and cancel button
        typingMessage.remove();
        removeCancelButton();
        
        // Clear request timeout
        clearRequestTimeout();
        
        console.log("Response status:", response.status);
        
        // Handle different response status codes
        if (response.status === 503) {
            // Service unavailable - DeepSeek API is down
            addMessage('system', currentLanguage === 'en' ? 
                `Our AI service is currently experiencing high demand. Please try again in a few moments.` : 
                `Dịch vụ AI của chúng tôi hiện đang có lượng truy cập cao. Vui lòng thử lại sau vài phút.`);
            return;
        } else if (response.status === 504) {
            // Gateway timeout - Vercel function timed out
            addMessage('system', currentLanguage === 'en' ? 
                `Request timed out. Our AI service is taking longer than expected. Please try a shorter message or try again later.` : 
                `Yêu cầu đã hết thời gian chờ. Dịch vụ AI của chúng tôi đang mất nhiều thời gian hơn dự kiến. Vui lòng thử một tin nhắn ngắn hơn.`);
            return;
        } else if (!response.ok) {
            // Get error details
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText.substring(0, 100)}`);
        }
        
        // Parse the response
        let data;
        try {
            const responseText = await response.text();
            data = JSON.parse(responseText);
        } catch (e) {
            console.error("Error parsing JSON response:", e);
            throw new Error(`Invalid response from server`);
        }
        
        console.log("Parsed response data:", data);
        
        // Update session ID and current request ID
        if (data.session_id) {
            sessionId = data.session_id;
        }
        
        if (data.request_id) {
            currentRequestId = data.request_id;
        }
        
        // Add performance info if available
        if (data.elapsed_ms) {
            console.log(`Response generated in ${data.elapsed_ms}ms using ${data.tokens || 'unknown'} tokens`);
        }
        
        // Add agent response to chat
        addMessage('agent', data.response || data.error || 'Sorry, I couldn\'t generate a response.');
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Handle abort/timeout errors specifically
        if (error.name === 'AbortError' || error.message.includes('timed out')) {
            addMessage('system', currentLanguage === 'en' ? 
                'The request timed out. Please try a shorter message or try again later.' : 
                'Yêu cầu đã hết thời gian chờ. Vui lòng thử với tin nhắn ngắn hơn hoặc thử lại sau.');
        } else {
            // Handle other errors
            addMessage('system', currentLanguage === 'en' ? 
                `I'm having trouble connecting right now. Please try again in a moment.` : 
                `Tôi đang gặp sự cố kết nối. Vui lòng thử lại sau một lát.`);
        }
        
    } finally {
        // Always clean up
        isSending = false;
        sendButton.disabled = false;
        currentRequestId = null;
        
        if (typingMessage && typingMessage.parentNode) {
            typingMessage.remove();
        }
        
        removeCancelButton();
        clearRequestTimeout();
        scrollToBottom();
    }
}

function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatHistory.appendChild(messageDiv);
    
    scrollToBottom();
    return messageDiv;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'agent');
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('typing-indicator');
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        contentDiv.appendChild(dot);
    }
    
    messageDiv.appendChild(contentDiv);
    chatHistory.appendChild(messageDiv);
    
    scrollToBottom();
    return messageDiv;
}

function addCancelButton() {
    const cancelButton = document.createElement('button');
    cancelButton.classList.add('cancel-button');
    cancelButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <span class="lang-content" data-lang-en="Cancel" data-lang-vi="Hủy">Cancel</span>
    `;
    
    cancelButton.id = 'cancel-request-button';
    
    // Add to the page
    const inputArea = document.querySelector('.input-area');
    inputArea.appendChild(cancelButton);
    
    // Apply language
    updateElementLanguage(cancelButton);
    
    return cancelButton;
}

function removeCancelButton() {
    const cancelButton = document.getElementById('cancel-request-button');
    if (cancelButton) {
        cancelButton.remove();
    }
}

function setupRequestTimeout() {
    // Clear any existing timeout
    clearRequestTimeout();
    
    // Set up staged user feedback for long-running requests
    requestTimeoutId = setTimeout(() => {
        // First feedback after USER_FEEDBACK_TIMEOUT
        const statusMsg = addMessage('system', currentLanguage === 'en' ? 
            'This may take a moment...' : 
            'Điều này có thể mất một chút thời gian...');
            
        // Second feedback after LONG_WAIT_WARNING
        requestTimeoutId = setTimeout(() => {
            statusMsg.remove(); // Remove the first message
            
            addMessage('system', currentLanguage === 'en' ? 
                'Our AI service is thinking... thanks for your patience.' : 
                'Dịch vụ AI của chúng tôi đang suy nghĩ... cảm ơn sự kiên nhẫn của bạn.');
                
        }, LONG_WAIT_WARNING - USER_FEEDBACK_TIMEOUT);
        
    }, USER_FEEDBACK_TIMEOUT);
}

function clearRequestTimeout() {
    if (requestTimeoutId) {
        clearTimeout(requestTimeoutId);
        requestTimeoutId = null;
    }
}

function showToolCalls(toolCalls) {
    // Clear previous tool calls
    toolCallsContainer.innerHTML = '';
    
    toolCalls.forEach(call => {
        const toolDiv = document.createElement('div');
        toolDiv.classList.add('tool-call');
        
        const nameDiv = document.createElement('div');
        nameDiv.classList.add('tool-name');
        nameDiv.textContent = `Tool: ${call.tool}`;
        
        const argsDiv = document.createElement('div');
        argsDiv.classList.add('tool-args');
        argsDiv.textContent = JSON.stringify(call.args, null, 2);
        
        const resultDiv = document.createElement('div');
        resultDiv.classList.add('tool-result');
        resultDiv.textContent = call.result;
        
        toolDiv.appendChild(nameDiv);
        toolDiv.appendChild(argsDiv);
        toolDiv.appendChild(resultDiv);
        
        toolCallsContainer.appendChild(toolDiv);
    });
    
    toolContainer.classList.remove('hidden');
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Functions - Tabs

function switchTab(tabName) {
    // Update active tab button
    tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Show selected tab content
    tabContents.forEach(content => {
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Functions - Content Templates

function showTemplateForm(templateType) {
    // Set form title based on template type
    let title;
    
    switch (templateType) {
        case 'social_post':
            title = currentLanguage === 'en' ? 'Create Social Post' : 'Tạo Bài Đăng MXH';
            templatePlatformField.classList.remove('hidden');
            break;
        case 'blog_post':
            title = currentLanguage === 'en' ? 'Create Blog Article' : 'Tạo Bài Viết Blog';
            break;
        case 'email':
            title = currentLanguage === 'en' ? 'Create Marketing Email' : 'Tạo Email Marketing';
            break;
        case 'ad_copy':
            title = currentLanguage === 'en' ? 'Create Ad Copy' : 'Tạo Nội Dung Quảng Cáo';
            break;
        default:
            title = currentLanguage === 'en' ? 'Create Content' : 'Tạo Nội Dung';
            templatePlatformField.classList.add('hidden');
    }
    
    templateFormTitle.textContent = title;
    
    // Store template type for later
    templateForm.setAttribute('data-template-type', templateType);
    
    // Clear form fields
    templateTopic.value = '';
    templatePlatform.value = '';
    templateLength.value = 'medium';
    templateKeywords.value = '';
    templateCta.value = '';
    
    // Show the form
    templateForm.classList.remove('hidden');
}

function hideTemplateForm() {
    templateForm.classList.add('hidden');
}

async function generateContent() {
    const templateType = templateForm.getAttribute('data-template-type');
    const briefName = templateBriefSelect.value || 'tony_tech_insights_brief';
    const topic = templateTopic.value.trim();
    const platform = templatePlatformField.classList.contains('hidden') ? null : templatePlatform.value;
    const length = templateLength.value;
    const keywords = templateKeywords.value.trim();
    const cta = templateCta.value.trim();
    
    // Validate required fields
    if (!topic) {
        alert(currentLanguage === 'en' ? 'Please enter a topic' : 'Vui lòng nhập chủ đề');
        return;
    }
    
    if (templateType === 'social_post' && platform === '') {
        alert(currentLanguage === 'en' ? 'Please select a platform for the social post' : 'Vui lòng chọn nền tảng cho bài đăng');
        return;
    }
    
    // Warn if DeepSeek is not connected
    if (!isDeepSeekConnected) {
        const proceed = confirm(currentLanguage === 'en' ? 
            'The AI service is currently unavailable, so content generation may be limited. Would you like to proceed anyway?' : 
            'Dịch vụ AI hiện không khả dụng, vì vậy việc tạo nội dung có thể bị hạn chế. Bạn có muốn tiếp tục không?');
        
        if (!proceed) {
            return;
        }
    }
    
    // Build prompt
    let prompt = `Generate a ${templateType.replace('_', ' ')} about "${topic}" `;
    prompt += `using the brand brief "${briefName}" `;
    
    if (platform) {
        prompt += `for ${platform} `;
    }
    
    prompt += `with ${length} length. `;
    
    if (keywords) {
        prompt += `Include these keywords: ${keywords}. `;
    }
    
    if (cta) {
        prompt += `Use this call to action: "${cta}". `;
    }
    
    // Add language preference
    prompt += `Please provide the content in ${currentLanguage === 'en' ? 'English' : 'Vietnamese'}.`;
    
    try {
        // Switch to chat tab first 
        switchTab('chat');
        
        // Add user message
        addMessage('user', prompt);
        
        // Display typing indicator
        const typingMessage = addTypingIndicator();
        
        // Hide the template form
        hideTemplateForm();
        
        // Add cancel button
        const cancelButton = addCancelButton();
        cancelButton.addEventListener('click', handleRequestCancel);
        
        // Set up request timeout monitoring with feedback for templates
        setupRequestTimeout(60000); // 1 minute timeout for templates
        
        // Create timeout message immediately for templates since we know they'll take time
        const timeoutMessage = document.createElement('div');
        timeoutMessage.classList.add('timeout-warning');
        timeoutMessage.textContent = currentLanguage === 'en' ? 
            'Generating content for you now...' : 
            'Đang tạo nội dung cho bạn...';
        
        // Add timeout message immediately for templates
        if (typingMessage.parentElement) {
            typingMessage.parentElement.insertBefore(timeoutMessage, typingMessage);
        }
        
        // Send request to API with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt,
                session_id: sessionId
            }),
            signal: controller.signal
        }).finally(() => {
            clearTimeout(timeoutId);
        });
        
        // Remove typing indicator and timeout message
        typingMessage.remove();
        if (timeoutMessage.parentElement) {
            timeoutMessage.remove();
        }
        
        // Remove cancel button
        removeCancelButton();
        
        // Clear request timeout
        clearRequestTimeout();
        
        // Get the response text regardless of status
        const responseText = await response.text();
        console.log("Raw template response:", responseText);
        
        // Check if the response was ok
        if (!response.ok) {
            console.error(`API error ${response.status}: ${responseText}`);
            
            // Parse the error if possible
            let errorData;
            try {
                errorData = JSON.parse(responseText);
            } catch (e) {
                errorData = { error: `Status ${response.status}: ${responseText}` };
            }
            
            // Show specific error message
            addMessage('system', currentLanguage === 'en' ? 
                `Sorry, there was a problem generating the content. Please try again in a moment.` : 
                `Xin lỗi, đã xảy ra sự cố khi tạo nội dung. Vui lòng thử lại sau một lát.`);
                
            throw new Error(`API error: ${response.status} - ${responseText.substring(0, 100)}`);
        }
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error("Error parsing JSON response:", e);
            throw new Error(`Invalid JSON response from server: ${responseText.substring(0, 100)}`);
        }
        
        console.log("Parsed template response data:", data);
        
        // Check if using fallback response
        if (data.using_deepseek === false) {
            addMessage('system', currentLanguage === 'en' ? 
                `Note: I've provided a basic template. For more detailed content, please try again when the AI service is fully available.` : 
                `Lưu ý: Tôi đã cung cấp một mẫu cơ bản. Để có nội dung chi tiết hơn, vui lòng thử lại khi dịch vụ AI hoàn toàn khả dụng.`);
        }
        
        // Add agent response
        addMessage('agent', data.response);
        
        // Show tool calls if any
        if (data.tool_calls && data.tool_calls.length > 0) {
            showToolCalls(data.tool_calls);
        } else {
            toolContainer.classList.add('hidden');
        }
        
    } catch (error) {
        console.error('Error generating content:', error);
        
        if (error.name === 'AbortError') {
            // Handle timeout/abort error specifically
            addMessage('system', currentLanguage === 'en' ? 
                'The content generation request took too long and was cancelled. Please try again in a moment.' : 
                'Yêu cầu tạo nội dung mất quá nhiều thời gian và đã bị hủy. Vui lòng thử lại sau một lát.');
        } else {
            // Handle other errors
            addMessage('error', `Error: ${error.message}`);
        }
    } finally {
        removeCancelButton();
        clearRequestTimeout();
        isSending = false;
        sendButton.disabled = false;
        currentRequestId = null;
        scrollToBottom();
    }
}

// Add welcome message
setTimeout(() => {
    const welcomeMsg = currentLanguage === 'en' 
        ? 'Tip: Click on "Content Templates" to quickly generate branded content for Tony Tech Insights!'
        : 'Mẹo: Nhấp vào "Mẫu Tạo Nội Dung" để nhanh chóng tạo nội dung có thương hiệu cho Tony Tech Insights!';
    addMessage('system', welcomeMsg);
}, 1000);

async function handleRequestCancel() {
    // User canceled the request
    clearRequestTimeout();
    
    // Mark as no longer sending
    isSending = false;
    sendButton.disabled = false;
    
    // Remove typing indicator
    const typingIndicators = document.querySelectorAll('.typing-indicator');
    typingIndicators.forEach(indicator => {
        if (indicator.parentNode && indicator.parentNode.classList.contains('message')) {
            indicator.parentNode.remove();
        }
    });
    
    // Remove cancel button
    removeCancelButton();
    
    // Show cancellation message
    addMessage('system', currentLanguage === 'en' ? 
        'Request canceled.' : 
        'Yêu cầu đã bị hủy.');
} 