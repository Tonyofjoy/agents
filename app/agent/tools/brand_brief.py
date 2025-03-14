"""
Brand Brief Tool for the DeepSeek Agent.
This tool allows loading and analyzing company brand briefs to inform content generation.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import uuid
import glob

from langchain.tools import BaseTool

# Storage for brand briefs (in-memory for simplicity)
BRAND_BRIEFS = {
    "tony_tech_insights_brief": {
        "company_name": "Tony Tech Insights",
        "tagline": "Affordable technology solutions for small businesses",
        "mission": "To provide small businesses with affordable and accessible technology solutions that drive growth and efficiency",
        "values": ["Innovation", "Accessibility", "Reliability", "Expertise", "Customer-focus"],
        "tone_of_voice": ["Professional", "Approachable", "Knowledgeable", "Clear", "Helpful"],
        "target_audience": [
            {"name": "Small Business Owners", "description": "Entrepreneurs and small business owners with limited IT resources"},
            {"name": "IT Decision Makers", "description": "Managers responsible for technology decisions in small to medium businesses"}
        ],
        "unique_selling_proposition": "Expert IT solutions tailored for small businesses at affordable prices",
        "brand_colors": ["#0056b3", "#00aa66", "#333333"],
        "competitors": ["Enterprise IT firms", "Generic IT support providers", "DIY solutions"],
        "content_topics": ["Cybersecurity", "Cloud Solutions", "IT Infrastructure", "Digital Transformation", "Cost-Effective Technology"],
        "taboo_topics": ["Political views", "Religious opinions", "Controversial social issues"]
    },
    "mai_phu_hung_brief": {
        "company_name": "Mai Phú Hưng",
        "tagline": "Chất lượng sản phẩm - Dịch vụ hoàn hảo",
        "mission": "Trở thành biểu tượng hàng đầu của ngành hàng tiêu dùng Thái Lan chính hãng, chất lượng và phù hợp với túi tiền của gia đình Việt.",
        "vision": "Bằng khát vọng nâng cao chất lượng cuộc sống của mọi người, Mai Phú Hưng bước tiến trở thành doanh nghiệp dẫn đầu Việt Nam về sản phẩm tiêu dùng Thái Lan.",
        "values": ["Chất lượng", "Tin cậy", "Hiệu quả", "Phục vụ khách hàng", "Đổi mới", "Phát triển bền vững"],
        "tone_of_voice": ["Nhiệt tình", "Thân thiện", "Ấm áp", "Tự hào"],
        "target_audience": [
            {"name": "Các đại lý phân phối hàng tiêu dùng", "description": "Các đơn vị phân phối sản phẩm tiêu dùng tại Việt Nam"},
            {"name": "Cửa hàng bách hóa", "description": "Các cửa hàng bán lẻ sản phẩm gia dụng và chăm sóc nhà cửa"},
            {"name": "Tạp hóa truyền thống", "description": "Các cửa hàng tạp hóa trong khu dân cư"},
            {"name": "Nhà cung cấp trung gian", "description": "Các đơn vị trung gian trong chuỗi cung ứng"},
            {"name": "Siêu thị và chuỗi bán lẻ", "description": "Các hệ thống siêu thị và chuỗi cửa hàng bán lẻ"}
        ],
        "unique_selling_proposition": "Đứng đầu thị trường sỉ hàng Thái tại Thành phố Hồ Chí Minh với uy tín xây dựng qua nhiều năm hoạt động và mức độ hài lòng cao từ các đối tác kinh doanh.",
        "brand_colors": [
            {"name": "Vàng đồng", "hex": "#ca993b", "description": "Thể hiện sự sang trọng, uy tín và giá trị bền vững"},
            {"name": "Xanh dương đậm", "hex": "#2e3b63", "description": "Tượng trưng cho sự đáng tin cậy, chuyên nghiệp và ổn định"}
        ],
        "competitors": ["Blue Hà Thành", "Các nhà phân phối sỉ khác trong thị trường hàng Thái Lan"],
        "content_topics": [
            "Sản phẩm tiêu dùng Thái Lan", 
            "Chất lượng sản phẩm nhập khẩu", 
            "Giải pháp vệ sinh nhà cửa", 
            "Cơ hội kinh doanh và đại lý",
            "Các chương trình khuyến mãi", 
            "Chỉ dẫn sử dụng sản phẩm"
        ],
        "taboo_topics": [
            "So sánh tiêu cực với đối thủ", 
            "Chính trị", 
            "Vấn đề tôn giáo",
            "Giá cả không minh bạch"
        ],
        "products": [
            {"category": "Vệ sinh nhà cửa", "items": ["Nước giặt Thái Lan", "Nước xả Thái Lan", "Nước tẩy bồn cầu Thái Lan"]},
            {"category": "Thương hiệu phân phối", "items": ["Fineline", "SPJ", "Hygiene", "Dnne", "Comfort", "Fresh and Soft", "Blue", "Vaseline"]}
        ],
        "business_goals": [
            "Trở thành nhà phân phối hàng Thái số 1 Việt Nam",
            "Mở rộng mạng lưới phân phối trên toàn quốc",
            "Đa dạng hóa danh mục sản phẩm Thái Lan chính hãng",
            "Tăng cường nhận diện thương hiệu trong ngành hàng tiêu dùng",
            "Xây dựng quan hệ bền vững với các nhà sản xuất Thái Lan"
        ],
        "brand_promise": "Mai Phú Hưng cam kết cung cấp các sản phẩm tiêu dùng Thái Lan chính hãng, chất lượng cao với giá cả phù hợp, đồng thời mang đến dịch vụ chuyên nghiệp, nhiệt tình cho các đối tác kinh doanh, góp phần nâng cao chất lượng cuộc sống của người tiêu dùng Việt Nam.",
        "preferred_hashtags": [
            "daily", 
            "nhaphanphoi", 
            "maiphuhung", 
            "nuocruachen", 
            "sanphamgiadung",
            "thuonghieuViet",
            "HàngThái",
            "ChínhHãng"
        ],
        "communication_style": {
            "use_emojis": True,
            "bullet_points": True,
            "highlight_benefits": True,
            "include_contact": True,
            "emphasize_quality": True
        },
        "typography": {
            "primary_font": "Quicksand",
            "description": "Hiện đại, rõ ràng, dễ đọc và thân thiện"
        },
        "contact_info": {
            "company_name": "Công ty TNHH Mai Phú Hưng",
            "hotline": "0933.664.223 - 079.886.8886",
            "customer_service": "0898.338.883 - 0778.800.900",
            "website": "maiphuhung.com",
            "address": "31 Dân Tộc, P Tân Thành, Q Tân Phú, TP. Hồ Chí Minh",
            "social_media": {
                "facebook": "facebook.com/maiphuhungofficial",
                "instagram": "instagram.com/maiphuhungvn"
            }
        },
        "language_preference": "vi"
    }
}


class BrandBriefInput(BaseModel):
    """Input for the brand brief tool."""
    
    operation: str = Field(
        ..., 
        description="Operation to perform: 'save', 'get', 'list', or 'delete'"
    )
    
    brief_name: Optional[str] = Field(
        None, 
        description="Name of the brand brief"
    )
    
    content: Optional[Dict[str, Any]] = Field(
        None, 
        description="Content of the brand brief when operation is 'save'"
    )


class BrandBriefTool(BaseTool):
    """Tool for managing brand briefs."""
    
    name = "brand_brief"
    description = """
    Use this tool to save, retrieve, list, or delete company brand briefs.
    A brand brief contains important information about a company's brand identity, 
    tone of voice, target audience, value proposition, and other branding elements.
    This information is essential for generating on-brand content.
    """
    
    args_schema = BrandBriefInput
    
    def _run(self, operation: str, brief_name: Optional[str] = None, 
             content: Optional[Dict[str, Any]] = None) -> str:
        """Run the brand brief tool."""
        return self._async_run(operation, brief_name, content)
    
    async def _arun(self, operation: str, brief_name: Optional[str] = None, 
                   content: Optional[Dict[str, Any]] = None) -> str:
        """Run the brand brief tool asynchronously."""
        if operation == "save":
            return self._save_brief(brief_name, content)
        elif operation == "get":
            return self._get_brief(brief_name)
        elif operation == "list":
            return self._list_briefs()
        elif operation == "delete":
            return self._delete_brief(brief_name)
        else:
            return f"Invalid operation: {operation}. Supported operations are 'save', 'get', 'list', or 'delete'."
    
    def _save_brief(self, brief_name: Optional[str], content: Optional[Dict[str, Any]]) -> str:
        """Save a brand brief."""
        if not brief_name:
            brief_name = f"brief_{uuid.uuid4().hex[:8]}"
        
        if not content:
            return "Error: No content provided for the brand brief."
        
        # Ensure the brief has all necessary fields
        required_fields = [
            "company_name", 
            "tagline", 
            "mission", 
            "values", 
            "tone_of_voice", 
            "target_audience",
            "unique_selling_proposition"
        ]
        
        missing_fields = [field for field in required_fields if field not in content]
        
        if missing_fields:
            suggested_structure = {
                "company_name": "Your company name",
                "tagline": "Your tagline or slogan",
                "mission": "Your company mission statement",
                "values": ["Value 1", "Value 2", "Value 3"],
                "tone_of_voice": ["Professional", "Friendly", "Authoritative"],
                "target_audience": [
                    {"name": "Persona 1", "description": "Description of persona 1"},
                    {"name": "Persona 2", "description": "Description of persona 2"}
                ],
                "unique_selling_proposition": "What makes your company unique",
                "brand_colors": ["#HEXCODE1", "#HEXCODE2"],
                "competitors": ["Competitor 1", "Competitor 2"],
                "content_topics": ["Topic 1", "Topic 2", "Topic 3"],
                "taboo_topics": ["Topic to avoid 1", "Topic to avoid 2"]
            }
            
            return f"Error: The following required fields are missing: {', '.join(missing_fields)}. " + \
                   f"Suggested structure: {json.dumps(suggested_structure, indent=2)}"
        
        # Save the brief
        BRAND_BRIEFS[brief_name] = content
        
        return f"Brand brief '{brief_name}' saved successfully."
    
    def _get_brief(self, brief_name: Optional[str]) -> str:
        """Get a brand brief by name."""
        if not brief_name:
            return "Error: No brief name provided."
        
        if brief_name not in BRAND_BRIEFS:
            return f"Error: Brand brief '{brief_name}' not found."
        
        return json.dumps(BRAND_BRIEFS[brief_name], indent=2)
    
    def _list_briefs(self) -> str:
        """List all available brand briefs."""
        if not BRAND_BRIEFS:
            return "No brand briefs found."
        
        brief_list = "\n".join([f"- {name}" for name in BRAND_BRIEFS.keys()])
        return f"Available brand briefs:\n{brief_list}"
    
    def _delete_brief(self, brief_name: Optional[str]) -> str:
        """Delete a brand brief by name."""
        if not brief_name:
            return "Error: No brief name provided."
        
        if brief_name not in BRAND_BRIEFS:
            return f"Error: Brand brief '{brief_name}' not found."
        
        del BRAND_BRIEFS[brief_name]
        return f"Brand brief '{brief_name}' deleted successfully."

# Example Vietnamese brand brief
MAI_PHU_HUNG_BRIEF = {
    "company_name": "Mai Phú Hưng",
    "industry": "Household products",
    "description": "Mai Phú Hưng specializes in eco-friendly household and personal care products, focusing on natural ingredients and sustainability.",
    "brand_values": [
        "Natural ingredients",
        "Eco-friendly production",
        "Family safety",
        "Vietnamese heritage",
        "Quality and effectiveness"
    ],
    "tone_of_voice": [
        "Friendly and enthusiastic",
        "Educational about natural ingredients",
        "Warm and family-oriented",
        "Proud of Vietnamese heritage",
        "Straightforward about benefits"
    ],
    "target_audience": [
        "Vietnamese families with children",
        "Health-conscious consumers",
        "Environmentally-aware shoppers",
        "Middle to upper-middle class urban households"
    ],
    "preferred_hashtags": [
        "MaiPhuHung",
        "SạchTựNhiên",
        "SảnPhẩmVietNam",
        "ChấtLượngCuộcSống",
        "VìGiađình",
        "SứcKhỏeGiađình"
    ],
    "special_instructions": [
        "Always include product benefits related to health or environmental impact",
        "Emphasize the natural ingredients in products",
        "Include contact information: Website: maiphuhung.com.vn, Hotline: 028 7308 6680",
        "Vietnamese language should be primary, but can include some English terms when appropriate",
        "Use emojis in social media content for better engagement"
    ],
    "use_emojis": True,
    "contact_info": {
        "website": "maiphuhung.com.vn",
        "hotline": "028 7308 6680",
        "facebook": "MaiPhuHungVN",
        "zalo": "MaiPhuHung"
    },
    "language": "vi"
}

# Save the brief to a file
def _save_mai_phu_hung_brief():
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(tools_dir, "mai_phu_hung_brief.json"), 'w', encoding='utf-8') as f:
        json.dump(MAI_PHU_HUNG_BRIEF, f, ensure_ascii=False, indent=4)

# Ensure the brief is available
_save_mai_phu_hung_brief() 