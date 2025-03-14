const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for terminal output
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  reset: '\x1b[0m'
};

console.log(`${colors.blue}Starting DeepSeek Agent Cursor Plugin installation...${colors.reset}`);

// Check if npm is installed
try {
  console.log(`${colors.yellow}Checking if npm is installed...${colors.reset}`);
  execSync('npm --version', { stdio: 'ignore' });
  console.log(`${colors.green}npm is installed.${colors.reset}`);
} catch (error) {
  console.error(`${colors.red}Error: npm is not installed. Please install Node.js and npm first.${colors.reset}`);
  process.exit(1);
}

// Install dependencies
try {
  console.log(`${colors.yellow}Installing dependencies...${colors.reset}`);
  execSync('npm install', { stdio: 'inherit' });
  console.log(`${colors.green}Dependencies installed successfully.${colors.reset}`);
} catch (error) {
  console.error(`${colors.red}Error installing dependencies:${colors.reset}`, error.message);
  process.exit(1);
}

// Build the plugin
try {
  console.log(`${colors.yellow}Building the plugin...${colors.reset}`);
  execSync('npm run build', { stdio: 'inherit' });
  console.log(`${colors.green}Plugin built successfully.${colors.reset}`);
} catch (error) {
  console.error(`${colors.red}Error building the plugin:${colors.reset}`, error.message);
  process.exit(1);
}

// Check if dist directory exists
if (!fs.existsSync(path.join(__dirname, 'dist'))) {
  console.error(`${colors.red}Error: dist directory not found. Build may have failed.${colors.reset}`);
  process.exit(1);
}

console.log(`${colors.blue}Installation completed successfully!${colors.reset}`);
console.log(`${colors.green}To use the plugin in Cursor:${colors.reset}`);
console.log(`${colors.yellow}1. Make sure this directory is in your Cursor plugins folder${colors.reset}`);
console.log(`${colors.yellow}2. Restart Cursor${colors.reset}`);
console.log(`${colors.yellow}3. Use the command palette to access DeepSeek Agent commands${colors.reset}`); 