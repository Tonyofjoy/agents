// Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin + '/api';
let sessionId = generateSessionId(); // Initialize session ID immediately
let isSending = false;
let currentLanguage = 'en'; // Default language
let currentRequestId = null; // Track the current request ID for cancellation
let requestTimeoutId = null; // To track the timeout for long-running requests

// Updated timeouts
const FETCH_TIMEOUT = 40000; // 40 seconds timeout for fetch requests
const USER_FEEDBACK_TIMEOUT = 15000; // 15 seconds before showing "taking longer than expected" message

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
    // Connect to API
    await initChat();
    
    // Set initial language
    switchLanguage(currentLanguage);
}

async function initChat() {
    try {
        console.log("Connecting to API at:", API_URL);
        console.log("Initial session ID:", sessionId);
        
        // Test connection to API
        const response = await fetch(`${API_URL}`);
        console.log("API response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`API returned status ${response.status}`);
        }
        
        const data = await response.json();
        console.log("API response data:", data);
        
        if (data.status === 'ok') {
            statusElement.textContent = 'Connected';
            statusElement.classList.add('connected');
            statusElement.classList.remove('disconnected');
            
            // Session ID is already initialized at the top
            console.log('Using session ID:', sessionId);
        } else {
            throw new Error('API not responding correctly');
        }
    } catch (error) {
        console.error('Error connecting to API:', error);
        statusElement.textContent = 'Disconnected';
        statusElement.classList.remove('connected');
        statusElement.classList.add('disconnected');
        
        addMessage('system', `Error connecting to the Tony Tech Insights API. Make sure the server is running.`);
        
        // Add more detailed error information
        console.log("API URL:", API_URL);
        console.log("Window location:", window.location.href);
        console.log("Will use fallback session ID:", sessionId);
        
        // Try connecting to the base URL
        try {
            console.log("Attempting to connect to base URL:", window.location.origin);
            const baseResponse = await fetch(window.location.origin);
            console.log("Base URL response status:", baseResponse.status);
        } catch (baseError) {
            console.error("Error connecting to base URL:", baseError);
        }
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
    
    // Clear input
    userInput.value = '';
    
    // Add user message to chat
    addMessage('user', messageText);
    
    // Disable send button
    isSending = true;
    sendButton.disabled = true;
    
    // Add typing indicator
    const typingMessage = addTypingIndicator();
    
    // Add cancel button
    const cancelButton = addCancelButton();
    cancelButton.addEventListener('click', handleRequestCancel);
    
    // Set up request timeout monitoring
    setupRequestTimeout(120000); // 2 minutes timeout
    
    try {
        console.log("Sending message to API:", messageText);
        console.log("API URL for chat:", `${API_URL}/chat`);
        console.log("Session ID:", sessionId);
        
        // Ensure session ID is set
        if (!sessionId) {
            sessionId = generateSessionId();
            console.log("Generated new session ID:", sessionId);
        }
        
        // Prepare request payload
        const payload = {
            prompt: messageText,
            session_id: sessionId
        };
        
        console.log("Request payload:", payload);
        
        // Send request to API with increased timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT); // Increased from 25s to 40s
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        }).finally(() => clearTimeout(timeoutId));
        
        console.log("Response status:", response.status);
        
        // Remove typing indicator and cancel button
        typingMessage.remove();
        removeCancelButton();
        
        // Clear request timeout
        clearRequestTimeout();
        
        // Handle timeout (504) responses gracefully
        if (response.status === 504) {
            console.log("Server timeout, using fallback response");
            
            // Add a system message about the timeout
            addMessage('system', currentLanguage === 'en' ? 
                'The server took too long to respond. Here\'s a simple response instead:' : 
                'Máy chủ mất quá nhiều thời gian để phản hồi. Đây là phản hồi đơn giản thay thế:');
            
            // Create a fallback response
            const fallbackResponse = currentLanguage === 'en' ? 
                `I understand you're asking about "${messageText}". This is an important topic for businesses. Please try asking a more specific question for a better response.` :
                `Tôi hiểu bạn đang hỏi về "${messageText}". Đây là một chủ đề quan trọng cho doanh nghiệp. Vui lòng thử hỏi câu hỏi cụ thể hơn để có phản hồi tốt hơn.`;
            
            // Add the fallback response as an agent message
            addMessage('agent', fallbackResponse);
            
            // Early return to avoid processing the response
            return;
        }
        
        // Get the response text first, regardless of status code
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        
        // Then check if the response was ok
        if (!response.ok) {
            console.error(`API error ${response.status}: ${responseText}`);
            
            // Add error message to chat
            if (response.status === 404) {
                addMessage('system', 'Error: The chat API endpoint could not be found. This is likely a configuration issue with the API routes.');
            } else if (response.status === 500) {
                addMessage('system', 'Error: The server encountered an internal error. Please check the server logs for details.');
            } else {
                addMessage('system', `Error: The server returned status code ${response.status}. Please try again later.`);
            }
            
            throw new Error(`API error: ${response.status} - ${responseText.substring(0, 100)}`);
        }
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error("Error parsing JSON response:", e);
            console.error("Raw response that couldn't be parsed:", responseText);
            addMessage('system', 'Error: The server returned an invalid response. Please try again later.');
            throw new Error(`Invalid JSON response from server: ${responseText.substring(0, 100)}`);
        }
        
        console.log("Parsed response data:", data);
        
        // Check if using fallback and notify user if appropriate
        if (data._using_fallback || data.using_deepseek === false) {
            console.log("Using fallback response mechanism");
            if (data._error) {
                console.error("Original error:", data._error);
            }
            
            // Only add system message for non-Vietnamese content as it might be confusing
            if (currentLanguage === 'en' && !messageText.includes('Vietnamese')) {
                addMessage('system', "Note: I'm providing a simplified response due to technical limitations. For better results, try a more specific question.");
            }
        }
        
        // Update session ID and current request ID
        sessionId = data.session_id;
        currentRequestId = data.request_id;
        
        // Add agent response to chat
        addMessage('agent', data.response);
        
        // Show tool calls if any
        if (data.tool_calls && data.tool_calls.length > 0) {
            showToolCalls(data.tool_calls);
        } else {
            toolContainer.classList.add('hidden');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Handle abort/timeout errors specifically
        if (error.name === 'AbortError') {
            addMessage('system', currentLanguage === 'en' ? 
                'The request was cancelled because it took too long. Please try a shorter message or try again later.' : 
                'Yêu cầu đã bị hủy vì mất quá nhiều thời gian. Vui lòng thử tin nhắn ngắn hơn hoặc thử lại sau.');
        } else {
            // Handle other errors
            addMessage('error', `Error: ${error.message}`);
        }
        
        removeCancelButton();
        clearRequestTimeout();
    } finally {
        isSending = false;
        sendButton.disabled = false;
        currentRequestId = null;
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

function setupRequestTimeout(timeoutMs) {
    // Clear any existing timeout
    clearRequestTimeout();
    
    // Set a short timeout for first warning
    requestTimeoutId = setTimeout(() => {
        if (isSending && currentRequestId) {
            // Add a message to let the user know the request is taking a while
            const timeoutWarning = document.createElement('div');
            timeoutWarning.classList.add('timeout-warning');
            timeoutWarning.id = 'timeout-warning';
            timeoutWarning.textContent = currentLanguage === 'en' ? 
                'I\'m working on a thoughtful response. This might take a moment...' : 
                'Tôi đang làm việc trên một phản hồi có chiều sâu. Việc này có thể mất một chút thời gian...';
            
            // Add to the chat just before the typing indicator
            const typingIndicator = document.querySelector('.typing-indicator');
            if (typingIndicator && typingIndicator.parentElement) {
                typingIndicator.parentElement.insertBefore(timeoutWarning, typingIndicator);
            }
            
            // Set a longer timeout for follow-up warning (45 seconds)
            setTimeout(() => {
                if (isSending && currentRequestId) {
                    // Update the warning
                    const existingWarning = document.getElementById('timeout-warning');
                    if (existingWarning) {
                        existingWarning.textContent = currentLanguage === 'en' ? 
                            'This request is taking longer than expected. You can cancel and try a simpler query, or continue waiting for a detailed response.' : 
                            'Yêu cầu này đang mất nhiều thời gian hơn dự kiến. Bạn có thể hủy và thử một yêu cầu đơn giản hơn, hoặc tiếp tục chờ để nhận phản hồi chi tiết.';
                        existingWarning.style.backgroundColor = '#fff8e1';
                        existingWarning.style.color = '#856404';
                        existingWarning.style.borderColor = '#ffeeba';
                    }
                }
            }, 30000); // 30 seconds after first warning (45 seconds total)
        }
    }, USER_FEEDBACK_TIMEOUT); // Show first message after 15 seconds (reduced from 30)
}

function clearRequestTimeout() {
    if (requestTimeoutId) {
        clearTimeout(requestTimeoutId);
        requestTimeoutId = null;
    }
    
    // Remove any timeout warning messages
    const timeoutWarnings = document.querySelectorAll('.timeout-warning');
    timeoutWarnings.forEach(warning => warning.remove());
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
        setupRequestTimeout(180000); // 3 minutes timeout for templates since they're more complex
        
        // Create timeout message immediately for templates since we know they'll take time
        const timeoutMessage = document.createElement('div');
        timeoutMessage.classList.add('timeout-warning');
        timeoutMessage.textContent = currentLanguage === 'en' ? 
            'Generating creative content. This typically takes 20-45 seconds for quality results...' : 
            'Đang tạo nội dung sáng tạo. Điều này thường mất 20-45 giây để có kết quả chất lượng...';
        
        // Add timeout message after 2 seconds for templates
        const messageTimeoutId = setTimeout(() => {
            if (typingMessage.parentElement) {
                typingMessage.parentElement.insertBefore(timeoutMessage, typingMessage);
            }
        }, 2000);
        
        // Send request to API with increased timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT); // 40 seconds timeout (increased from 25s)
        
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
            clearTimeout(messageTimeoutId);
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
        
        if (!response.ok) {
            // If it's a server timeout (504), add a more user-friendly message
            if (response.status === 504) {
                addMessage('system', currentLanguage === 'en' ? 
                    'The content generation request timed out. I\'ll create a simpler response for you.' : 
                    'Yêu cầu tạo nội dung đã hết thời gian. Tôi sẽ tạo một phản hồi đơn giản hơn cho bạn.');
                
                // Generate fallback content
                let fallbackContent = `# ${topic.charAt(0).toUpperCase() + topic.slice(1)}: ${currentLanguage === 'en' ? 'Business Insights' : 'Hiểu biết về kinh doanh'}\n\n`;
                fallbackContent += currentLanguage === 'en' ?
                    `Here's a brief overview of ${topic} for your ${templateType.replace('_', ' ')}:\n\n` :
                    `Đây là tổng quan ngắn gọn về ${topic} cho ${templateType.replace('_', ' ')} của bạn:\n\n`;
                
                fallbackContent += currentLanguage === 'en' ?
                    `${topic} is transforming how businesses operate in today's digital landscape. Organizations that effectively leverage this technology gain significant advantages through improved efficiency, better customer experiences, and innovative business models.\n\n` :
                    `${topic} đang thay đổi cách các doanh nghiệp hoạt động trong bối cảnh kỹ thuật số ngày nay. Các tổ chức tận dụng hiệu quả công nghệ này đạt được lợi thế đáng kể thông qua hiệu quả được cải thiện, trải nghiệm khách hàng tốt hơn và các mô hình kinh doanh sáng tạo.\n\n`;
                
                fallbackContent += "Tony Tech Insights | " + (currentLanguage === 'en' ? "Making Technology Accessible for Every Business" : "Làm cho Công nghệ Tiếp cận với Mọi Doanh nghiệp");
                
                addMessage('agent', fallbackContent);
                return;
            }
            
            throw new Error(`API error: ${response.status}`);
        }
        
        // Get the response text first, regardless of status code
        const responseText = await response.text();
        console.log("Raw template response:", responseText);
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error("Error parsing JSON response:", e);
            throw new Error(`Invalid JSON response from server: ${responseText.substring(0, 100)}`);
        }
        
        console.log("Parsed template response data:", data);
        
        // Check if using fallback
        if (data._using_fallback || data.using_deepseek === false) {
            console.log("Using fallback response for template");
            // No need to notify user since templates are expected to be simplified sometimes
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
                'The request took too long to complete. Please try again with a simpler request or try later when the server is less busy.' : 
                'Yêu cầu mất quá nhiều thời gian để hoàn thành. Vui lòng thử lại với yêu cầu đơn giản hơn hoặc thử lại sau khi máy chủ ít bận rộn hơn.');
        } else {
            // Handle other errors
            addMessage('error', `Error: ${error.message}`);
            addMessage('system', currentLanguage === 'en' ?
                'There was a problem generating your content. Please try again later.' :
                'Đã xảy ra sự cố khi tạo nội dung của bạn. Vui lòng thử lại sau.');
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
    if (!currentRequestId) {
        return;
    }
    
    try {
        statusElement.textContent = currentLanguage === 'en' ? 'Cancelling...' : 'Đang hủy...';
        
        // Disable the cancel button while cancellation is processing
        const cancelButton = document.getElementById('cancel-request-button');
        if (cancelButton) {
            cancelButton.disabled = true;
            cancelButton.textContent = currentLanguage === 'en' ? 'Cancelling...' : 'Đang hủy...';
        }
        
        const response = await fetch(`${API_URL}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                request_id: currentRequestId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`Request cancelled: ${currentRequestId}`);
            statusElement.textContent = currentLanguage === 'en' ? 'Connected' : 'Đã kết nối';
            
            // Remove typing indicator
            const typingIndicator = document.querySelector('.typing-indicator');
            if (typingIndicator) {
                typingIndicator.parentElement.remove();
            }
            
            // Add cancellation message
            addMessage('system', currentLanguage === 'en' ? 
                'Request cancelled. You can continue the conversation.' : 
                'Yêu cầu đã bị hủy. Bạn có thể tiếp tục cuộc trò chuyện.');
        } else {
            console.error(`Failed to cancel request: ${data.message}`);
            // If cancellation fails but the request was already done
            if (data.message.includes("already completed")) {
                // The request might have completed while we were trying to cancel
                statusElement.textContent = currentLanguage === 'en' ? 'Connected' : 'Đã kết nối';
            } else {
                // Some other error occurred
                addMessage('error', currentLanguage === 'en' ? 
                    `Failed to cancel request: ${data.message}` : 
                    `Không thể hủy yêu cầu: ${data.message}`);
            }
        }
    } catch (error) {
        console.error('Error cancelling request:', error);
        addMessage('error', currentLanguage === 'en' ? 
            `Error cancelling request: ${error.message}` : 
            `Lỗi khi hủy yêu cầu: ${error.message}`);
    } finally {
        removeCancelButton();
        clearRequestTimeout();
        isSending = false;
        sendButton.disabled = false;
        currentRequestId = null;
    }
} 