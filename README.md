# Mai Phú Hưng Content Creator

A web-based AI content creation assistant specialized for generating marketing content for Mai Phú Hưng brand, powered by DeepSeek API.

## Features

- **AI-Powered Content Creation**: Generate social media posts, blog articles, marketing emails, and ad copy
- **Brand-Aligned Content**: Maintains consistent voice, tone, and messaging for Mai Phú Hưng brand
- **Template System**: Quick access to content generation templates
- **Bilingual Support**: Vietnamese and English language interfaces
- **Content Database**: References examples from content library for consistent style

## Requirements

- Python 3.8+
- Node.js (for local frontend development)
- DeepSeek API key

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agents.git
   cd agents
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file and set your DeepSeek API key and other configurations.

5. Run the backend server:
   ```bash
   cd app
   python main.py
   ```

6. In a new terminal, start the frontend server:
   ```bash
   cd frontend
   npm install
   node server.js
   ```

7. Access the application at `http://localhost:3000`

## GitHub and Vercel Deployment

### Preparing for GitHub

1. Initialize Git repository (if not already done):
   ```bash
   git init
   ```

2. Add all files to the repository:
   ```bash
   git add .
   ```

3. Create your first commit:
   ```bash
   git commit -m "Initial commit"
   ```

4. Create a new repository on GitHub named "agents"

5. Connect your local repository to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/agents.git
   ```

6. Push your code to GitHub:
   ```bash
   git push -u origin main
   ```

### Deploying to Vercel

1. Sign up for a Vercel account if you don't have one: https://vercel.com/signup

2. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

3. Log in to Vercel:
   ```bash
   vercel login
   ```

4. Deploy to Vercel:
   ```bash
   vercel
   ```

5. When prompted, select the following options:
   - Link to existing project: No
   - Project name: agents
   - Directory: ./ (root directory)

6. Set up environment variables in the Vercel dashboard:
   - DEEPSEEK_API_KEY: Your DeepSeek API key

7. Once deployed, your application will be available at a Vercel URL.

## API Usage

### Chat Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "prompt": "Create a social media post about natural cleaners",
  "session_id": "123456"  // Optional, will be generated if not provided
}
```

Response:

```json
{
  "response": "Content of the generated social media post",
  "session_id": "123456",
  "tool_calls": []
}
```

## License

MIT 