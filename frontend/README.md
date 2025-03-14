# DeepSeek Content Creator

A powerful web interface for generating brand-aligned content using the DeepSeek AI Agent API.

## Features

- **Brand Brief Management**: Create, edit, and manage your company's brand briefs
- **Content Generation**: Generate various types of content based on your brand briefs:
  - Social media posts for different platforms
  - Blog articles with structured sections
  - Marketing emails with strong CTAs
  - Advertising copy for campaigns
  - Product descriptions
  - Attention-grabbing headlines
- **Chat Interface**: Interact directly with the AI assistant
- **Template System**: Quick access templates for different content types
- **Responsive Design**: Works on mobile and desktop

## Setup and Usage

1. Make sure the DeepSeek API server is running at http://localhost:8000
   ```
   cd ..
   python -m app.main
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Start the frontend server
   ```
   npm start
   ```

4. Open your browser and go to http://localhost:3000

## Using the Content Creator

### Managing Brand Briefs

1. Go to the "Brand Brief" tab
2. Click "Create New Brief" to create a custom brief or "Load Sample Brief" to start with a template
3. Fill in the JSON structure with your brand information:
   - Company name and tagline
   - Mission and values
   - Tone of voice
   - Target audience
   - Unique selling proposition
4. Click "Save Brief" to store your brief
5. You can view or delete saved briefs using the "List Saved Briefs" option

### Generating Content

#### Using Templates:

1. Go to the "Content Templates" tab
2. Select the type of content you want to create
3. Fill in the form:
   - Select your brand brief
   - Enter a topic
   - Choose platform (for social posts)
   - Set length and other parameters
4. Click "Generate Content"

#### Using Chat:

1. Go to the "Chat" tab
2. Ask the AI to create specific content using your brief
   - Example: "Create a LinkedIn post about sustainability using the EcoTech brief"
   - Example: "Write a blog post about cloud computing for TechCorp"

## Customization

- By default, the interface connects to the API at `http://localhost:8000`
- You can modify the API URL in `script.js` if needed
- The sample brand brief can be edited in `app/agent/tools/sample_brand_brief.json`

## Implementation Details

The content generation system works through two main tools:

1. **brand_brief**: Manages the storage and retrieval of brand information
2. **content_generator**: Creates content based on brand briefs and user specifications

When generating content, the system:
1. References the brand brief for tone, values, and target audience
2. Applies content-type specific best practices (character limits, structures, etc.)
3. Incorporates user-specified parameters (topic, keywords, CTAs)

## Notes

This is a demonstration implementation. For production use, you would want to add:

- Authentication and user accounts
- Database storage for briefs and generated content 
- Content history and organization
- Advanced customization options
- Streaming responses
- Direct API endpoints for each function 