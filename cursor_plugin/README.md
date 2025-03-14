# DeepSeek Agent Cursor Plugin

A plugin for the Cursor IDE that allows you to interact with your DeepSeek AI Agent.

## Features

- **Generate Code**: Generate code snippets based on your description
- **Explain Code**: Get detailed explanations of selected code 
- **Refactor Code**: Automatically refactor selected code based on your requirements
- **Configure API Endpoint**: Set the endpoint to your running DeepSeek Agent API

## Installation

### Option 1: Automated Installation (Recommended)

1. Copy this plugin directory to your Cursor plugins folder
2. Run: `node install.js` or `npm run install-plugin`
3. Enable the plugin in Cursor

### Option 2: Manual Installation

1. Copy this plugin directory to your Cursor plugins folder
2. Install dependencies: `npm install`
3. Build the plugin: `npm run build`
4. Enable the plugin in Cursor

## Usage

### Generate Code

1. Place your cursor where you want to insert code
2. Use the command palette and select "DeepSeek Agent: Generate Code"
3. Enter a description of the code you want to generate
4. The code will be generated and inserted at your cursor position

### Explain Code

1. Select the code you want to understand
2. Use the command palette and select "DeepSeek Agent: Explain Code"
3. A detailed explanation of the code will be shown

### Refactor Code

1. Select the code you want to refactor
2. Use the command palette and select "DeepSeek Agent: Refactor Code"
3. Enter your refactoring instructions
4. The selected code will be replaced with the refactored version

### Configure API Endpoint

1. Use the command palette and select "DeepSeek Agent: Configure Endpoint"
2. Enter the URL of your DeepSeek Agent API (default: http://localhost:8000/chat)

## Requirements

- Cursor IDE
- Running DeepSeek Agent API (from the main project)

## Configuration

You can modify the `index.ts` file to customize the plugin behavior: 

## Troubleshooting

### Common Issues

1. **"tsc is not recognized as an internal or external command"**
   - This error occurs when TypeScript is not properly installed. Run `npm install` before running `npm run build`.

2. **TypeScript compilation errors**
   - If you see errors related to implicit 'any' types, make sure to add proper type annotations in the code.
   - You can temporarily disable strict type checking in tsconfig.json by setting `"strict": false`.

3. **API Connection Issues**
   - Verify that your DeepSeek Agent API is running and accessible.
   - Check the API endpoint configuration in the plugin.
   - Ensure your network allows the connection to the specified API endpoint.

4. **Plugin Not Appearing in Cursor**
   - Make sure the plugin is correctly built (`npm run build`).
   - Verify that the plugin directory is in the correct Cursor plugins folder.
   - Restart Cursor after installing or updating the plugin.

5. **Axios Request Errors**
   - Check the DeepSeek Agent API logs for server-side errors.
   - Verify that the API is properly processing and returning responses.
   - Ensure CORS is configured correctly on the API server.

For additional help, please check the main DeepSeek Agent repository or submit an issue. 