"""
Content Generator Tool for the DeepSeek Agent.
This tool generates various types of content aligned with a company's brand.
"""

import json
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.agent.tools.brand_brief import BRAND_BRIEFS


class ContentGeneratorInput(BaseModel):
    """Input for the content generator tool."""
    
    content_type: str = Field(
        ...,
        description="Type of content to generate: 'social_post', 'blog_post', 'email', 'ad_copy', 'product_description', 'headline'"
    )
    
    brief_name: str = Field(
        ...,
        description="Name of the brand brief to use for content generation"
    )
    
    topic: str = Field(
        ...,
        description="The main topic or subject of the content"
    )
    
    platform: Optional[str] = Field(
        None,
        description="Platform for social posts (e.g., 'twitter', 'linkedin', 'instagram', 'facebook')"
    )
    
    length: Optional[str] = Field(
        "medium",
        description="Length of the content: 'short', 'medium', or 'long'"
    )
    
    keywords: Optional[List[str]] = Field(
        None,
        description="Keywords to include in the content"
    )
    
    call_to_action: Optional[str] = Field(
        None,
        description="Call to action for the content"
    )
    
    language: Optional[str] = Field(
        "en",
        description="Language for the content: 'en' for English, 'vi' for Vietnamese, etc."
    )
    
    include_contact_info: Optional[bool] = Field(
        False,
        description="Whether to include contact information section in the content"
    )
    
    contact_info: Optional[Dict[str, str]] = Field(
        None,
        description="Contact information to include (company name, phone, email, website, address, etc.)"
    )
    
    use_emojis: Optional[bool] = Field(
        True,
        description="Whether to use emojis in the content"
    )


class ContentGeneratorTool(BaseTool):
    """Tool for generating branded content."""
    
    name = "content_generator"
    description = """
    Use this tool to generate various types of content aligned with a company's brand.
    Available content types:
    - social_post: Create social media posts for different platforms
    - blog_post: Generate blog articles with various sections
    - email: Craft marketing or newsletter emails
    - ad_copy: Write advertising copy for campaigns
    - product_description: Create compelling product descriptions
    - headline: Generate attention-grabbing headlines
    
    The content will be tailored based on the specified brand brief.
    You can specify the language for content (e.g., English, Vietnamese).
    For social posts, you can include contact information and emojis.
    """
    
    args_schema = ContentGeneratorInput
    
    def _run(self, content_type: str, brief_name: str, topic: str, platform: Optional[str] = None,
            length: Optional[str] = "medium", keywords: Optional[List[str]] = None,
            call_to_action: Optional[str] = None, language: Optional[str] = "en",
            include_contact_info: Optional[bool] = False, contact_info: Optional[Dict[str, str]] = None,
            use_emojis: Optional[bool] = True) -> str:
        """Run the content generator tool."""
        return self._async_run(content_type, brief_name, topic, platform, length, keywords, 
                              call_to_action, language, include_contact_info, contact_info, use_emojis)
    
    async def _arun(self, content_type: str, brief_name: str, topic: str, platform: Optional[str] = None,
                  length: Optional[str] = "medium", keywords: Optional[List[str]] = None,
                  call_to_action: Optional[str] = None, language: Optional[str] = "en",
                  include_contact_info: Optional[bool] = False, contact_info: Optional[Dict[str, str]] = None,
                  use_emojis: Optional[bool] = True) -> str:
        """Run the content generator tool asynchronously."""
        
        # Validate brief exists
        if brief_name not in BRAND_BRIEFS:
            return f"Error: Brand brief '{brief_name}' not found. Please create a brand brief first."
        
        # Get the brand brief
        brand_brief = BRAND_BRIEFS[brief_name]
        
        # Validate content type
        valid_content_types = ["social_post", "blog_post", "email", "ad_copy", "product_description", "headline"]
        if content_type not in valid_content_types:
            return f"Error: Invalid content type '{content_type}'. Valid types are: {', '.join(valid_content_types)}."
        
        # Validate length
        valid_lengths = ["short", "medium", "long"]
        if length not in valid_lengths:
            length = "medium"  # Default to medium if invalid
        
        # Validate platform for social posts
        if content_type == "social_post" and platform:
            valid_platforms = ["twitter", "linkedin", "instagram", "facebook"]
            if platform not in valid_platforms:
                return f"Error: Invalid platform '{platform}'. Valid platforms are: {', '.join(valid_platforms)}."
        
        # Generate content based on the type
        if content_type == "social_post":
            return self._generate_social_post(brand_brief, topic, platform, length, keywords, call_to_action, 
                                            language, include_contact_info, contact_info, use_emojis)
        elif content_type == "blog_post":
            return self._generate_blog_post(brand_brief, topic, length, keywords, call_to_action, language)
        elif content_type == "email":
            return self._generate_email(brand_brief, topic, length, keywords, call_to_action, language)
        elif content_type == "ad_copy":
            return self._generate_ad_copy(brand_brief, topic, length, keywords, call_to_action, language)
        elif content_type == "product_description":
            return self._generate_product_description(brand_brief, topic, length, keywords, language)
        elif content_type == "headline":
            return self._generate_headline(brand_brief, topic, keywords, language)
    
    def _generate_social_post(self, brand_brief: Dict[str, Any], topic: str, platform: Optional[str],
                             length: str, keywords: Optional[List[str]], call_to_action: Optional[str],
                             language: str = "en", include_contact_info: bool = False,
                             contact_info: Optional[Dict[str, str]] = None, use_emojis: bool = True) -> str:
        """Generate a social media post."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Platform-specific considerations
        char_limit = None
        platform_features = []
        
        if platform == "twitter":
            char_limit = 280
            platform_features = ["hashtags", "mentions", "link"]
        elif platform == "linkedin":
            platform_features = ["professional tone", "industry insights", "link", "hashtags"]
        elif platform == "instagram":
            platform_features = ["hashtags", "emojis", "visual description", "call to action"]
        elif platform == "facebook":
            platform_features = ["engaging question", "link", "call to action", "emojis"]
        
        # Length considerations
        if length == "short":
            word_count = "30-50 words"
        elif length == "medium":
            word_count = "50-100 words"
        else:  # long
            word_count = "100-150 words"
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese cultural context and expressions
- Include appropriate Vietnamese formatting for contact info (if required)
- Use Vietnamese social media conventions and trends
"""
        
        # Emoji usage
        emoji_instructions = ""
        if use_emojis:
            emoji_instructions = """
- Use relevant emojis to highlight key points and enhance engagement
- Place emojis at the beginning of important sections
- Use emojis that align with the brand's tone and the post's message
"""
        
        # Contact information section
        contact_section = ""
        if include_contact_info:
            contact_section = """
- Include a clear separator (like "---") before contact information
- Format contact information with relevant icons/emojis
- Structure contact info in a clean, easy-to-read format
- Include all provided contact methods (phone, email, website, address)
"""
            
            if contact_info:
                contact_details = "\n".join([f"  - {k}: {v}" for k, v in contact_info.items()])
                contact_section += f"\nCONTACT INFORMATION TO INCLUDE:\n{contact_details}\n"
        
        # Build instructions for content creation
        instructions = f"""
Create a {platform if platform else "social media"} post for {company_name} about {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}

CONTENT GUIDELINES:
- Length: {word_count}
{f"- Character limit: {char_limit} characters" if char_limit else ""}
- Include: {', '.join(platform_features) if platform else "engaging hook, value proposition"}
{f"- Keywords to include: {', '.join(keywords)}" if keywords else ""}
{f"- Call to action: {call_to_action}" if call_to_action else ""}
- Structure: Use clear sections with visual breaks (line spacing) between sections
- Formatting: Use bullet points or dashes for listing features/benefits
{emoji_instructions}
{contact_section}
{lang_specific}

CONTENT STRUCTURE:
1. Eye-catching headline/hook with emoji(s) if appropriate
2. Brief introduction to the topic/product
3. Key benefits or features (using bullet points)
4. Supporting details or unique selling points
5. Strong call to action
{f"6. Contact information section" if include_contact_info else ""}
7. Relevant hashtags

Create content that resonates with {brand_brief["company_name"]}'s target audience and reflects their brand values.
"""
        
        # This would typically make a call to the LLM, but for this example, 
        # we'll just return the instructions that would be sent to the LLM
        return f"SOCIAL POST GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate the actual social post content based on these instructions, using the DeepSeek API."
    
    def _generate_blog_post(self, brand_brief: Dict[str, Any], topic: str, length: str,
                           keywords: Optional[List[str]], call_to_action: Optional[str],
                           language: str = "en") -> str:
        """Generate a blog post."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Length considerations
        if length == "short":
            word_count = "300-500 words"
            sections = 3
        elif length == "medium":
            word_count = "700-1000 words"
            sections = 5
        else:  # long
            word_count = "1500-2000 words"
            sections = 7
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese cultural context and expressions
- Adapt formatting, punctuation, and tone for Vietnamese readers
"""
        
        # Build instructions
        instructions = f"""
Create a blog post for {company_name} about {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}

CONTENT STRUCTURE:
- Length: {word_count}
- Include {sections} distinct sections with subheadings
- Include an engaging introduction and conclusion
- Include practical tips or actionable insights
{f"- Keywords to include: {', '.join(keywords)}" if keywords else ""}
{f"- Call to action: {call_to_action}" if call_to_action else ""}
{lang_specific}

Create content that positions {brand_brief["company_name"]} as a thought leader while providing valuable insights to their target audience.
"""
        
        return f"BLOG POST GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate the actual blog post content based on these instructions, using the DeepSeek API."
    
    def _generate_email(self, brand_brief: Dict[str, Any], topic: str, length: str,
                       keywords: Optional[List[str]], call_to_action: Optional[str],
                       language: str = "en") -> str:
        """Generate a marketing or newsletter email."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese cultural context and expressions
- Use appropriate Vietnamese greetings and closings
- Adapt formatting and punctuation for Vietnamese readers
"""
        
        # Build instructions
        instructions = f"""
Create a marketing email for {company_name} about {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}

CONTENT STRUCTURE:
- Include an attention-grabbing subject line
- Include a personalized greeting
- Clear sections with scannable content
- Strong {call_to_action if call_to_action else "call to action"}
{f"- Keywords to include: {', '.join(keywords)}" if keywords else ""}
{lang_specific}

Create an email that engages the reader and encourages them to take action.
"""
        
        return f"EMAIL GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate the actual email content based on these instructions, using the DeepSeek API."
    
    def _generate_ad_copy(self, brand_brief: Dict[str, Any], topic: str, length: str,
                         keywords: Optional[List[str]], call_to_action: Optional[str],
                         language: str = "en") -> str:
        """Generate advertising copy."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese cultural context and advertising norms
- Adapt messaging for Vietnamese audience preferences
"""
        
        # Build instructions
        instructions = f"""
Create advertising copy for {company_name} about {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}
- Tagline: {brand_brief["tagline"]}

CONTENT GUIDELINES:
- Focus on benefits rather than features
- Include a strong {call_to_action if call_to_action else "call to action"}
- Address the target audience's pain points
{f"- Keywords to include: {', '.join(keywords)}" if keywords else ""}
{lang_specific}

Create compelling ad copy that drives action and highlights {company_name}'s unique value.
"""
        
        return f"AD COPY GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate the actual ad copy based on these instructions, using the DeepSeek API."
    
    def _generate_product_description(self, brand_brief: Dict[str, Any], topic: str, length: str,
                                     keywords: Optional[List[str]], language: str = "en") -> str:
        """Generate a product description."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese consumer preferences and product description norms
- Use appropriate Vietnamese product terminology
"""
        
        # Build instructions
        instructions = f"""
Create a product description for {company_name}'s {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}

CONTENT GUIDELINES:
- Highlight key features and benefits
- Address what problems it solves
- Include sensory words to create vivid imagery
- Include social proof or credibility indicators
{f"- Keywords to include: {', '.join(keywords)}" if keywords else ""}
{lang_specific}

Create a compelling product description that makes the reader want to learn more or purchase.
"""
        
        return f"PRODUCT DESCRIPTION GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate the actual product description based on these instructions, using the DeepSeek API."
    
    def _generate_headline(self, brand_brief: Dict[str, Any], topic: str, 
                          keywords: Optional[List[str]], language: str = "en") -> str:
        """Generate headlines or titles."""
        company_name = brand_brief["company_name"]
        tone = ", ".join(brand_brief["tone_of_voice"]) if isinstance(brand_brief["tone_of_voice"], list) else brand_brief["tone_of_voice"]
        
        # Language-specific features
        lang_specific = ""
        if language == "vi":
            lang_specific = """
- Use Vietnamese language throughout
- Consider Vietnamese headline conventions and cultural references
- Adapt headline structure for Vietnamese reading patterns
"""
        
        # Build instructions
        instructions = f"""
Create 5-7 compelling headline options for {company_name}'s content about {topic}.

BRAND VOICE:
- Tone: {tone}
- USP: {brand_brief["unique_selling_proposition"]}

HEADLINE GUIDELINES:
- Include a mix of question, how-to, list-based, and curiosity-driven headlines
- Keep each headline under 70 characters when possible
- Ensure headlines are clear, specific, and benefit-focused
{f"- Include key phrases where natural: {', '.join(keywords)}" if keywords else ""}
{lang_specific}

Create headlines that grab attention and drive interest in {company_name}'s content.
"""
        
        return f"HEADLINE GENERATION INSTRUCTIONS:\n{instructions}\n\nIn a real implementation, this would generate actual headline options based on these instructions, using the DeepSeek API." 