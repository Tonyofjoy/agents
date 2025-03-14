from http.server import BaseHTTPRequestHandler
import json
import uuid
import re
import random
import time

class handler(BaseHTTPRequestHandler):
    """
    Chat API endpoint handler.
    This endpoint handles chat requests from the frontend and returns responses.
    """
    
    def do_POST(self):
        """Handle POST request to the chat endpoint."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # Parse JSON body
            if request_body:
                body = json.loads(request_body)
                prompt = body.get("prompt", "")
                session_id = body.get("session_id") or str(uuid.uuid4())
            else:
                prompt = "Empty request"
                session_id = str(uuid.uuid4())
            
            # Check if this is a content template request
            if "Generate a " in prompt and " about " in prompt:
                response_text = self.generate_template_content(prompt)
            else:
                # Generate a meaningful response based on the prompt
                response_text = self.generate_response(prompt)
            
            # Create response
            response = {
                "response": response_text,
                "session_id": session_id,
                "tool_calls": [],
                "request_id": f"req_{uuid.uuid4().hex[:10]}"
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Handle errors
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS request for CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def generate_template_content(self, prompt):
        """
        Generate content based on templates specified in the prompt.
        Extracts content type, topic, and other parameters from the prompt.
        """
        # Extract content type
        content_type = None
        if "blog post" in prompt or "blog article" in prompt:
            content_type = "blog post"
        elif "social post" in prompt or "social media" in prompt:
            content_type = "social media post"
        elif "email" in prompt:
            content_type = "email"
        elif "ad copy" in prompt or "advertisement" in prompt:
            content_type = "ad copy"
        else:
            content_type = "content"
            
        # Extract topic
        topic_match = re.search(r'about "(.*?)"', prompt)
        topic = topic_match.group(1) if topic_match else "technology"
        
        # Extract length
        length = "medium"
        if "short" in prompt:
            length = "short"
        elif "long" in prompt:
            length = "long"
            
        # Extract keywords
        keywords = []
        keywords_match = re.search(r'keywords: (.*?)\.', prompt)
        if keywords_match:
            keywords_text = keywords_match.group(1)
            keywords = [k.strip() for k in keywords_text.split(',')]
            
        # Extract call to action
        cta = ""
        cta_match = re.search(r'call to action: "(.*?)"', prompt)
        if cta_match:
            cta = cta_match.group(1)
            
        # Extract platform for social media
        platform = ""
        if content_type == "social media post":
            if "LinkedIn" in prompt:
                platform = "LinkedIn"
            elif "Twitter" in prompt or "X" in prompt:
                platform = "Twitter"
            elif "Facebook" in prompt:
                platform = "Facebook"
            elif "Instagram" in prompt:
                platform = "Instagram"
                
        # Generate content based on type
        if content_type == "blog post":
            return self.generate_blog_post(topic, length, keywords, cta)
        elif content_type == "social media post":
            return self.generate_social_post(topic, platform, keywords, cta)
        elif content_type == "email":
            return self.generate_email(topic, length, keywords, cta)
        elif content_type == "ad copy":
            return self.generate_ad_copy(topic, keywords, cta)
        else:
            return self.generate_generic_content(topic, length, keywords, cta)
    
    def generate_blog_post(self, topic, length, keywords, cta):
        """Generate a blog post about the given topic."""
        # Current date for the blog post
        current_date = time.strftime("%B %d, %Y")
        
        # Determine post length
        if length == "short":
            paragraphs = 3
        elif length == "long":
            paragraphs = 7
        else:  # medium
            paragraphs = 5
            
        # Keywords mention
        keyword_text = ""
        if keywords:
            keyword_text = "Keywords: " + ", ".join(keywords) + "\n\n"
            
        # Title options based on topic
        title_templates = [
            f"The Ultimate Guide to {topic} for Business Growth",
            f"How {topic} is Transforming Business in {time.strftime('%Y')}",
            f"{topic}: What Every Business Owner Needs to Know",
            f"5 Ways {topic} Can Boost Your Business Performance",
            f"The Future of {topic}: Trends and Predictions"
        ]
        title = random.choice(title_templates)
        
        # Introduction
        intro = f"In today's rapidly evolving technological landscape, {topic} stands out as a critical factor for business success. Organizations that effectively leverage {topic} gain competitive advantages through improved efficiency, enhanced customer experiences, and innovative business models."
        
        # Body paragraphs
        body_templates = [
            f"{topic} enables businesses to streamline operations by automating routine tasks and reducing manual intervention. This not only saves time but also minimizes human error.",
            f"When implementing {topic} solutions, businesses should start with clear objectives and measurable goals. This ensures that technology investments align with strategic priorities.",
            f"The data generated through {topic} implementations provides valuable insights that can inform decision-making across all business functions.",
            f"Security considerations are paramount when adopting {topic} technologies. Protecting sensitive information and ensuring compliance with regulations should be top priorities.",
            f"Small and medium-sized businesses can benefit from {topic} just as much as large enterprises, often with more agility and less organizational resistance.",
            f"The cost of implementing {topic} solutions has decreased significantly in recent years, making advanced technologies accessible to businesses of all sizes.",
            f"Case studies across various industries demonstrate that successful {topic} adoption typically involves collaboration between IT teams and business units.",
            f"As {topic} continues to evolve, staying informed about emerging trends becomes crucial for maintaining competitive advantage.",
            f"Employee training and change management are often overlooked aspects of {topic} implementation but are critical for realizing the full potential of technology investments."
        ]
        
        # Select random paragraphs but maintain the first one as intro
        selected_paragraphs = random.sample(body_templates, min(paragraphs-2, len(body_templates)))
        
        # Conclusion with CTA if provided
        conclusion = f"As we move forward in the digital age, businesses that effectively harness the power of {topic} will be better positioned to thrive in an increasingly competitive marketplace."
        if cta:
            conclusion += f" {cta}"
            
        # Combine all parts
        blog_content = f"# {title}\n\n"
        blog_content += f"Published on {current_date}\n\n"
        blog_content += keyword_text
        blog_content += f"{intro}\n\n"
        
        for para in selected_paragraphs:
            blog_content += f"{para}\n\n"
            
        blog_content += f"{conclusion}\n\n"
        blog_content += f"---\n"
        blog_content += f"Tony Tech Insights | Making Technology Accessible for Every Business"
        
        return blog_content
    
    def generate_social_post(self, topic, platform, keywords, cta):
        """Generate a social media post about the given topic."""
        # Adjust content for platform
        hashtags = ""
        if keywords:
            hashtags = " ".join(["#" + kw.replace(" ", "") for kw in keywords])
            
        # Post content based on platform
        if platform == "LinkedIn":
            post = f"📊 **{topic.title()} Insights** 📊\n\n"
            post += f"In today's business environment, understanding {topic} is crucial for sustainable growth and innovation.\n\n"
            post += f"Three key considerations for businesses:\n"
            post += f"1️⃣ Evaluate how {topic} aligns with your strategic objectives\n"
            post += f"2️⃣ Invest in the right tools and talent to maximize ROI\n"
            post += f"3️⃣ Continuously measure and optimize your approach\n\n"
            
            if cta:
                post += f"{cta}\n\n"
                
            if hashtags:
                post += f"{hashtags}\n\n"
                
            post += "What's your experience with this technology? Share in the comments! 👇"
            
        elif platform == "Twitter":
            post = f"{topic.title()} is transforming how businesses operate and compete in the digital landscape.\n\n"
            
            if cta:
                post += f"{cta}\n\n"
                
            if hashtags:
                post += f"{hashtags}"
                
        elif platform == "Facebook" or platform == "Instagram":
            post = f"🚀 **{topic.title()} For Business Success** 🚀\n\n"
            post += f"Are you leveraging {topic} to its full potential? Here's why it matters for your business growth strategy:\n\n"
            post += f"✅ Improved operational efficiency\n"
            post += f"✅ Enhanced customer experiences\n"
            post += f"✅ Data-driven decision making\n\n"
            
            if cta:
                post += f"{cta}\n\n"
                
            if hashtags:
                post += f"{hashtags}"
        else:
            # Generic social post
            post = f"💡 **{topic.title()} Insights** 💡\n\n"
            post += f"Businesses that effectively leverage {topic} gain significant competitive advantages in today's digital landscape.\n\n"
            
            if cta:
                post += f"{cta}\n\n"
                
            if hashtags:
                post += f"{hashtags}"
                
        return post
    
    def generate_email(self, topic, length, keywords, cta):
        """Generate a marketing email about the given topic."""
        # Current date for the email
        current_date = time.strftime("%B %Y")
        
        # Email subject lines
        subject_templates = [
            f"Unlock the Power of {topic} for Your Business",
            f"{topic.title()} Strategies That Drive Results",
            f"Transform Your Business with {topic} Solutions",
            f"Stay Ahead of Competitors with {topic} Innovation",
            f"The {topic} Advantage: Why It Matters for Your Business"
        ]
        subject = random.choice(subject_templates)
        
        # Email greeting
        greeting = "Dear Valued Business Partner,"
        
        # Email body based on length
        if length == "short":
            body = f"I hope this email finds you well. I wanted to share some insights about how {topic} can benefit your business operations and strategic goals.\n\n"
            body += f"{topic.title()} has become a critical factor for business success in {current_date}. Companies that effectively implement these solutions report improved efficiency, better customer experiences, and increased revenue opportunities.\n\n"
            
            if cta:
                body += f"{cta}\n\n"
                
            body += "Looking forward to discussing how we can help you implement these solutions."
            
        elif length == "long":
            body = f"I hope this email finds you well. I wanted to take a moment to discuss how {topic} is revolutionizing the business landscape and present some opportunities for your organization.\n\n"
            body += f"As we navigate the complexities of today's market, {topic} has emerged as a key differentiator between thriving businesses and those struggling to keep pace. Here's why this matters to you:\n\n"
            body += f"1. **Operational Excellence**: {topic} streamlines processes, reduces manual intervention, and minimizes errors.\n\n"
            body += f"2. **Customer Insights**: Leverage data from {topic} to better understand and serve your customers.\n\n"
            body += f"3. **Competitive Advantage**: Stay ahead of industry trends by adopting cutting-edge {topic} solutions.\n\n"
            body += f"4. **Cost Efficiency**: Despite initial investment, {topic} typically delivers significant ROI through reduced operational costs.\n\n"
            body += f"5. **Future-Proofing**: Building capabilities in {topic} positions your business for long-term success.\n\n"
            
            if cta:
                body += f"{cta}\n\n"
                
            body += f"Would you be available for a brief call to discuss how Tony Tech Insights can help you implement {topic} solutions tailored to your specific business needs?\n\n"
            body += "I look forward to your response and the opportunity to contribute to your business success."
            
        else:  # medium
            body = f"I hope this email finds you well. I wanted to share some valuable insights about {topic} and how it can transform your business operations.\n\n"
            body += f"In today's competitive landscape, {topic} has become a crucial factor for business success. Companies that effectively leverage these solutions gain advantages through:\n\n"
            body += f"• Improved operational efficiency\n"
            body += f"• Enhanced customer experiences\n"
            body += f"• Data-driven decision making\n\n"
            body += f"At Tony Tech Insights, we've helped businesses like yours implement {topic} solutions that deliver measurable results and positive ROI.\n\n"
            
            if cta:
                body += f"{cta}\n\n"
                
            body += "I'd welcome the opportunity to discuss how we can help your organization harness the power of these technologies."
        
        # Email closing
        closing = "\n\nWarm regards,\n\nTony\nTony Tech Insights\nMaking Technology Accessible for Every Business"
        
        # Combine all parts
        email_content = f"**Subject:** {subject}\n\n"
        email_content += f"{greeting}\n\n"
        email_content += body
        email_content += closing
        
        return email_content
    
    def generate_ad_copy(self, topic, keywords, cta):
        """Generate advertising copy about the given topic."""
        # Headlines
        headline_templates = [
            f"Transform Your Business with {topic.title()}",
            f"Unlock Growth: {topic.title()} Solutions",
            f"{topic.title()}: The Competitive Edge Your Business Needs",
            f"Revolutionize Your Strategy with {topic.title()}",
            f"Maximize ROI with Smart {topic.title()} Implementation"
        ]
        headline = random.choice(headline_templates)
        
        # Main copy
        main_copy = f"In today's fast-paced digital landscape, businesses need {topic} solutions that deliver real results. Tony Tech Insights provides accessible, affordable technology expertise that helps you stay competitive."
        
        # Benefits section
        benefits = [
            f"✓ Streamlined operations through {topic} optimization",
            f"✓ Data-driven insights to inform strategic decisions",
            f"✓ Customized {topic} solutions for your specific business needs",
            f"✓ Expert implementation with minimal disruption",
            f"✓ Ongoing support to maximize your technology investment"
        ]
        
        # Select 3 random benefits
        selected_benefits = random.sample(benefits, min(3, len(benefits)))
        benefits_text = "\n".join(selected_benefits)
        
        # Call to action
        call_to_action = cta if cta else f"Contact us today to learn how {topic} can transform your business."
        
        # Combine all parts
        ad_copy = f"**{headline}**\n\n"
        ad_copy += f"{main_copy}\n\n"
        ad_copy += f"{benefits_text}\n\n"
        ad_copy += f"**{call_to_action}**\n\n"
        
        # Add keywords as hashtags if provided
        if keywords:
            hashtags = " ".join(["#" + kw.replace(" ", "") for kw in keywords])
            ad_copy += f"{hashtags}"
        
        return ad_copy
    
    def generate_generic_content(self, topic, length, keywords, cta):
        """Generate generic content when the type isn't specified."""
        content = f"# {topic.title()}: Business Insights\n\n"
        content += f"{topic} is transforming how businesses operate in the digital age. Companies that effectively implement these technologies gain competitive advantages through improved efficiency, better customer experiences, and innovative business models.\n\n"
        
        if length == "medium" or length == "long":
            content += f"Key considerations when implementing {topic} include:\n\n"
            content += f"1. **Strategic Alignment**: Ensure {topic} initiatives support your core business objectives\n"
            content += f"2. **Implementation Plan**: Develop a phased approach with clear milestones\n"
            content += f"3. **Team Training**: Invest in upskilling staff to maximize technology adoption\n"
            content += f"4. **ROI Measurement**: Define metrics to evaluate the impact on your business\n\n"
            
        if length == "long":
            content += f"Case studies across various industries demonstrate that successful {topic} adoption typically involves collaboration between IT teams and business units. The most effective implementations start with addressing specific pain points rather than implementing technology for its own sake.\n\n"
            content += f"Data security and privacy considerations should also be at the forefront of any {topic} initiative, especially with increasing regulatory requirements across global markets.\n\n"
            
        if cta:
            content += f"{cta}\n\n"
            
        if keywords:
            content += f"Related topics: {', '.join(keywords)}"
            
        return content
    
    def generate_response(self, prompt):
        """
        Generate a meaningful response based on the user's prompt.
        This is a simple rule-based approach that can be enhanced later.
        """
        prompt = prompt.lower()
        
        # Define knowledge base for tech topics
        tech_topics = {
            "ai": [
                "Artificial Intelligence (AI) is transforming businesses by automating tasks, providing insights from data, and enabling new customer experiences.",
                "For small businesses, AI can level the playing field by providing access to powerful tools previously only available to large corporations.",
                "Key AI applications for business include customer service chatbots, predictive analytics, and content generation."
            ],
            "blockchain": [
                "Blockchain technology offers businesses transparent and secure ways to track transactions and manage supply chains.",
                "Beyond cryptocurrency, blockchain is being used for smart contracts, digital identity verification, and secure record-keeping.",
                "Small businesses can leverage blockchain for secure payments, establishing trust with customers, and reducing fraud."
            ],
            "cloud computing": [
                "Cloud computing enables businesses to access computing resources on-demand without major upfront investments.",
                "The shift to cloud services helps businesses scale operations, enable remote work, and reduce IT maintenance costs.",
                "Small businesses benefit from cloud solutions through improved collaboration, data backup, and access to enterprise-grade applications."
            ],
            "cybersecurity": [
                "Cybersecurity is essential for businesses of all sizes to protect sensitive data and maintain customer trust.",
                "Common threats include phishing attacks, ransomware, and data breaches, which can be costly for unprepared businesses.",
                "Small businesses can improve security with regular updates, employee training, and implementing multi-factor authentication."
            ],
            "iot": [
                "The Internet of Things (IoT) connects devices to collect data and improve business operations and decision-making.",
                "IoT applications include inventory tracking, equipment monitoring, and gathering customer behavior insights.",
                "Small businesses can use IoT solutions to optimize energy usage, improve security, and enhance customer experiences."
            ],
            "social media": [
                "Social media provides businesses with platforms to build brand awareness, engage with customers, and drive sales.",
                "Effective social media strategies involve consistent posting, audience engagement, and content that resonates with your target market.",
                "Small businesses can leverage social media for cost-effective marketing, customer support, and community building."
            ],
            "digital marketing": [
                "Digital marketing encompasses online strategies like SEO, content marketing, and paid advertising to reach potential customers.",
                "Data-driven approaches allow businesses to measure campaign effectiveness and optimize their marketing spend.",
                "Small businesses can start with simple digital marketing techniques like local SEO and email campaigns to drive growth."
            ],
            "ecommerce": [
                "E-commerce continues to grow, offering businesses opportunities to reach customers globally without physical store limitations.",
                "Successful online stores focus on user experience, mobile optimization, and streamlined checkout processes.",
                "Small businesses can enter e-commerce through marketplaces like Etsy or Shopify before investing in custom solutions."
            ],
            "remote work": [
                "Remote work technology enables businesses to access talent regardless of location and offer flexibility to employees.",
                "Effective remote work setups require the right communication tools, clear processes, and focus on results rather than hours.",
                "Small businesses can benefit from remote work through reduced office costs and access to a wider talent pool."
            ]
        }
        
        # General responses for greetings
        greetings = ["hello", "hi", "hey", "greetings"]
        if any(greeting in prompt for greeting in greetings):
            return "Hello! I'm your Tony Tech Insights assistant. I can help you with information about technology trends, digital marketing, and how businesses can leverage innovation. What tech topic would you like to explore today?"
        
        # Check for content creation requests
        content_patterns = [
            (r"(create|write|generate).*?(blog|article)", "I'd be happy to help create a blog article. What specific tech topic would you like to focus on?"),
            (r"(create|write|generate).*?(social media|post)", "I can help draft social media content. Which platform is this for, and what key message would you like to convey?"),
            (r"(create|write|generate).*?(email|newsletter)", "I can assist with email content. What's the main purpose of this email - announcement, promotion, or educational content?"),
            (r"(create|write|generate).*?(ad|advertising)", "I'd be glad to help with advertising copy. What product or service are you promoting, and who is your target audience?")
        ]
        
        for pattern, response in content_patterns:
            if re.search(pattern, prompt):
                return response
        
        # Check for topic-specific questions
        for topic, responses in tech_topics.items():
            if topic in prompt or topic.replace(" ", "") in prompt.replace(" ", ""):
                return random.choice(responses)
        
        # If no specific topic is detected, provide a general response
        general_responses = [
            "At Tony Tech Insights, we focus on making technology accessible for businesses of all sizes. Could you specify which aspect of technology you're interested in learning more about?",
            "I can provide insights on various technology topics including AI, blockchain, cloud computing, cybersecurity, IoT, social media, digital marketing, e-commerce, and remote work. Which area would you like to explore?",
            "Technology is transforming how businesses operate. I'd be happy to discuss specific innovations that could benefit your business. What challenges are you currently facing?",
            "Looking for ways to leverage technology for your business? I can help with specific recommendations if you share more about your industry and goals."
        ]
        
        return random.choice(general_responses) 