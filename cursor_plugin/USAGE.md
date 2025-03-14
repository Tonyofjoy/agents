# DeepSeek Agent Cursor Plugin - Usage Guide

This document provides detailed instructions on how to use the DeepSeek Agent plugin for Cursor IDE.

## Prerequisites

Before using the plugin, ensure you have:

1. Cursor IDE installed on your computer
2. Node.js and npm installed
3. The DeepSeek Agent API running and accessible

## Installation Location

The plugin should be installed in your Cursor plugins directory:

- **Windows**: `%APPDATA%\Cursor\User\plugins\deepseek-agent-plugin`
- **macOS**: `~/Library/Application Support/Cursor/User/plugins/deepseek-agent-plugin`
- **Linux**: `~/.config/Cursor/User/plugins/deepseek-agent-plugin`

## Available Commands

The plugin adds the following commands to Cursor's command palette (press `Ctrl+Shift+P` or `Cmd+Shift+P` to open):

### 1. DeepSeek Agent: Generate Code

Use this command to generate code based on a description. The plugin will insert the generated code at your cursor position.

**Usage:**
1. Place your cursor where you want to insert the generated code
2. Open the command palette and search for "DeepSeek Agent: Generate Code"
3. Enter a description of the code you want to generate (e.g., "a function to sort an array of objects by a specific property")
4. Wait for the code to be generated and inserted

**Tips:**
- Be specific in your description for better results
- The plugin will try to detect the programming language based on the file extension

### 2. DeepSeek Agent: Explain Code

Use this command to get an explanation of selected code.

**Usage:**
1. Select the code you want to understand
2. Open the command palette and search for "DeepSeek Agent: Explain Code"
3. Wait for the explanation to appear in a quick pick panel

**Tips:**
- Select complete logical blocks of code for better explanations
- Include function signatures and context for more accurate explanations

### 3. DeepSeek Agent: Refactor Code

Use this command to refactor selected code based on your instructions.

**Usage:**
1. Select the code you want to refactor
2. Open the command palette and search for "DeepSeek Agent: Refactor Code"
3. Enter your refactoring instructions (e.g., "optimize for performance" or "make it more readable")
4. Wait for the refactored code to replace your selection

**Tips:**
- Be specific about what aspect of the code you want to improve
- Review the changes after refactoring to ensure they meet your requirements

### 4. DeepSeek Agent: Configure Endpoint

Use this command to change the API endpoint URL for the DeepSeek Agent.

**Usage:**
1. Open the command palette and search for "DeepSeek Agent: Configure Endpoint"
2. Enter the full URL of your DeepSeek Agent API endpoint
3. A notification will confirm the update

**Default endpoint:** `https://agents-git-main-duongdang-tonytechinsis-projects.vercel.app/api/chat`

## Troubleshooting

If you encounter issues:

1. Ensure the plugin is correctly installed and built
2. Check that your DeepSeek Agent API is running and accessible
3. Try configuring a different API endpoint if the default isn't working
4. Restart Cursor after making changes to the plugin

## Session Management

The plugin maintains a session with the DeepSeek Agent API. This allows for context-aware interactions across multiple commands within the same Cursor session.

## Customization

To customize the plugin's behavior:

1. Open the `src/index.ts` file
2. Modify the relevant sections
3. Rebuild the plugin using `npm run build`
4. Restart Cursor to apply the changes

## Additional Resources

- Check the `README.md` file for basic information
- Refer to the main DeepSeek Agent documentation for API details
- Use the installation script (`install.js`) to update or reinstall the plugin

Happy coding with DeepSeek Agent! 