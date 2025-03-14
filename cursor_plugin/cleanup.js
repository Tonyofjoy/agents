const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for terminal output
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  reset: '\x1b[0m'
};

console.log(`${colors.blue}Starting DeepSeek Agent Cursor Plugin cleanup...${colors.reset}`);

// Directories to clean
const cleanDirs = ['dist', 'node_modules'];

// Clean dist directory
if (fs.existsSync(path.join(__dirname, 'dist'))) {
  try {
    console.log(`${colors.yellow}Removing dist directory...${colors.reset}`);
    fs.rmSync(path.join(__dirname, 'dist'), { recursive: true, force: true });
    console.log(`${colors.green}Dist directory removed successfully.${colors.reset}`);
  } catch (error) {
    console.error(`${colors.red}Error removing dist directory:${colors.reset}`, error.message);
  }
} else {
  console.log(`${colors.yellow}Dist directory not found, skipping.${colors.reset}`);
}

// Clean node_modules directory
const cleanNodeModules = () => {
  if (fs.existsSync(path.join(__dirname, 'node_modules'))) {
    try {
      console.log(`${colors.yellow}Removing node_modules directory...${colors.reset}`);
      fs.rmSync(path.join(__dirname, 'node_modules'), { recursive: true, force: true });
      console.log(`${colors.green}Node modules removed successfully.${colors.reset}`);
    } catch (error) {
      console.error(`${colors.red}Error removing node_modules directory:${colors.reset}`, error.message);
      console.log(`${colors.yellow}Trying alternative method...${colors.reset}`);
      try {
        execSync('rm -rf node_modules', { stdio: 'inherit' });
        console.log(`${colors.green}Node modules removed successfully.${colors.reset}`);
      } catch (altError) {
        console.error(`${colors.red}Failed to remove node_modules:${colors.reset}`, altError.message);
      }
    }
  } else {
    console.log(`${colors.yellow}Node_modules directory not found, skipping.${colors.reset}`);
  }
};

// Ask for confirmation before removing node_modules
if (process.argv.includes('--all')) {
  cleanNodeModules();
} else {
  console.log(`${colors.yellow}To remove node_modules directory, run with --all flag.${colors.reset}`);
}

// Clean package-lock.json
if (fs.existsSync(path.join(__dirname, 'package-lock.json'))) {
  try {
    console.log(`${colors.yellow}Removing package-lock.json...${colors.reset}`);
    fs.unlinkSync(path.join(__dirname, 'package-lock.json'));
    console.log(`${colors.green}Package-lock.json removed successfully.${colors.reset}`);
  } catch (error) {
    console.error(`${colors.red}Error removing package-lock.json:${colors.reset}`, error.message);
  }
} else {
  console.log(`${colors.yellow}Package-lock.json not found, skipping.${colors.reset}`);
}

console.log(`${colors.blue}Cleanup completed!${colors.reset}`);
console.log(`${colors.green}You can now reinstall the plugin with 'node install.js'${colors.reset}`); 