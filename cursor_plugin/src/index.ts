import axios from 'axios';

// Declare cursor API available in the extension environment
declare global {
  const cursor: {
    commands: {
      registerCommand: (name: string, callback: (...args: any[]) => any) => any;
    };
    notifications: {
      show: (message: string) => void;
    };
    input: {
      requestInput: (options: any) => Promise<string | undefined>;
    };
    showQuickPick: (options: any) => Promise<any>;
    activeTextEditor: any | undefined;
  };
}

// Define the configuration interface
interface DeepSeekAgentConfig {
  apiEndpoint: string;
  sessionId?: string;
}

// Default configuration
const DEFAULT_CONFIG: DeepSeekAgentConfig = {
  apiEndpoint: 'https://agents-git-main-duongdang-tonytechinsis-projects.vercel.app/api/chat',
};

// Define the request and response interfaces
interface ChatRequest {
  prompt: string;
  session_id?: string;
}

interface ChatResponse {
  response: string;
  session_id: string;
  tool_calls: any[];
}

// Store the plugin configuration
let config: DeepSeekAgentConfig = { ...DEFAULT_CONFIG };
// Store the current session ID
let currentSessionId: string | undefined = undefined;

/**
 * Initialize the plugin
 */
export function activate(context: any) {
  // Register the plugin commands
  context.subscriptions.push(
    cursor.commands.registerCommand('deepseekAgent.generateCode', generateCode),
    cursor.commands.registerCommand('deepseekAgent.explainCode', explainCode),
    cursor.commands.registerCommand('deepseekAgent.refactorCode', refactorCode),
    cursor.commands.registerCommand('deepseekAgent.configureEndpoint', configureEndpoint)
  );

  // Log activation message
  console.log('DeepSeek Agent plugin activated');
}

/**
 * Configure the API endpoint
 */
async function configureEndpoint() {
  const inputOptions = {
    title: 'DeepSeek Agent API Endpoint',
    placeHolder: config.apiEndpoint,
    prompt: 'Enter the API endpoint URL',
  };

  const endpoint = await cursor.input.requestInput(inputOptions);
  
  if (endpoint) {
    config.apiEndpoint = endpoint;
    cursor.notifications.show('DeepSeek Agent endpoint updated');
  }
}

/**
 * Send a request to the DeepSeek Agent API
 */
async function sendToAgent(prompt: string): Promise<ChatResponse> {
  try {
    const request: ChatRequest = {
      prompt,
      session_id: currentSessionId,
    };

    const response = await axios.post<ChatResponse>(
      config.apiEndpoint,
      request,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    // Save the session ID for subsequent requests
    currentSessionId = response.data.session_id;
    
    return response.data;
  } catch (error) {
    console.error('Error calling DeepSeek Agent API:', error);
    throw new Error('Failed to communicate with DeepSeek Agent API');
  }
}

/**
 * Generate code using the agent
 */
async function generateCode() {
  // Get the active editor
  const editor = cursor.activeTextEditor;
  if (!editor) {
    cursor.notifications.show('No active editor');
    return;
  }

  // Get user input for what code to generate
  const inputOptions = {
    title: 'Generate Code',
    placeHolder: 'Describe the code you want to generate',
    prompt: 'What code would you like me to generate?',
  };

  const userInput = await cursor.input.requestInput(inputOptions);
  
  if (!userInput) {
    return; // User cancelled
  }

  // Show progress notification
  cursor.notifications.show('Generating code with DeepSeek Agent...');

  try {
    // Send request to the agent
    const fileExtension = editor.document.fileName.split('.').pop() || '';
    const languageMap: { [key: string]: string } = {
      'js': 'JavaScript',
      'ts': 'TypeScript',
      'py': 'Python',
      'java': 'Java',
      'cpp': 'C++',
      'cs': 'C#',
      'go': 'Go',
      'rb': 'Ruby',
      'php': 'PHP',
      'swift': 'Swift',
      'kt': 'Kotlin',
      'rs': 'Rust',
    };
    
    const detectedLanguage = languageMap[fileExtension] || fileExtension;
    
    const prompt = `Generate the following code in ${detectedLanguage}: ${userInput}`;
    const response = await sendToAgent(prompt);

    // Insert the generated code at cursor position
    const position = editor.selection.active;
    editor.edit((editBuilder: any) => {
      editBuilder.insert(position, response.response);
    });

    cursor.notifications.show('Code generated successfully');
  } catch (error) {
    cursor.notifications.show('Failed to generate code: ' + (error as Error).message);
  }
}

/**
 * Explain the selected code
 */
async function explainCode() {
  // Get the active editor
  const editor = cursor.activeTextEditor;
  if (!editor) {
    cursor.notifications.show('No active editor');
    return;
  }

  // Get the selected text
  const selection = editor.selection;
  const selectedText = editor.document.getText(selection);
  
  if (!selectedText) {
    cursor.notifications.show('No code selected');
    return;
  }

  // Show progress notification
  cursor.notifications.show('Analyzing code with DeepSeek Agent...');

  try {
    // Send request to the agent
    const prompt = `Explain this code in detail:\n\`\`\`\n${selectedText}\n\`\`\``;
    const response = await sendToAgent(prompt);

    // Show the explanation
    cursor.showQuickPick({
      title: 'Code Explanation',
      items: [{ label: response.response }],
    });
  } catch (error) {
    cursor.notifications.show('Failed to explain code: ' + (error as Error).message);
  }
}

/**
 * Refactor the selected code
 */
async function refactorCode() {
  // Get the active editor
  const editor = cursor.activeTextEditor;
  if (!editor) {
    cursor.notifications.show('No active editor');
    return;
  }

  // Get the selected text
  const selection = editor.selection;
  const selectedText = editor.document.getText(selection);
  
  if (!selectedText) {
    cursor.notifications.show('No code selected');
    return;
  }

  // Get user input for refactoring instructions
  const inputOptions = {
    title: 'Refactor Code',
    placeHolder: 'E.g., Improve performance, Increase readability',
    prompt: 'How would you like to refactor this code?',
  };

  const userInput = await cursor.input.requestInput(inputOptions);
  
  if (!userInput) {
    return; // User cancelled
  }

  // Show progress notification
  cursor.notifications.show('Refactoring code with DeepSeek Agent...');

  try {
    // Send request to the agent
    const prompt = `Refactor this code to ${userInput}:\n\`\`\`\n${selectedText}\n\`\`\``;
    const response = await sendToAgent(prompt);

    // Replace the selected text with the refactored code
    editor.edit((editBuilder: any) => {
      editBuilder.replace(selection, response.response);
    });

    cursor.notifications.show('Code refactored successfully');
  } catch (error) {
    cursor.notifications.show('Failed to refactor code: ' + (error as Error).message);
  }
}

/**
 * Deactivate the plugin
 */
export function deactivate() {
  console.log('DeepSeek Agent plugin deactivated');
} 