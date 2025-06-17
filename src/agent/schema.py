from pydantic import BaseModel, Field
from typing import List, Optional, Annotated, Any
from langchain_core.messages import BaseMessage
import operator

class BrandInfo(BaseModel):
    company_name: str
    website: str
    region: Optional[str] = Field(None, description="The region of the brand's headquarters. Examples: 'United States', 'Canada', 'United Kingdom', 'Australia', 'New Zealand', 'Europe', 'Asia', 'Africa', 'South America', 'North America', 'Oceania' etc.")
    language: str = Field("English", description="The primary language the user is thinking and searching in. E.g., 'English', 'Turkish', 'Spanish', 'Mandarin Chinese'.")

class Perspective(BaseModel):
    """
    A detailed persona representing a user approaching an AI search engine. 
    This is used to generate a diverse and strategic set of prompts.
    """
    intent: str = Field(..., description="The user's high-level goal. What do they want to achieve? E.g., 'Make a purchase decision', 'Solve a technical problem', 'Conduct competitive research', 'Explore a new hobby'.")

    demographic: str = Field(None, description="The user's demographic profile. E.g., 'University Student', 'Young Professional', 'Retiree', 'Small Business Owner', 'Suburban Parent'.")

    region: Optional[str] = Field(None, description="The user's geographic location, which influences local context and availability. E.g., 'Atlanta, GA, USA', 'Istanbul, Turkey', 'Rural France', 'Southeast Asia'.")

    gender: Optional[str] = Field(None, description="The user's gender, only if it is a primary factor in their search. E.g., 'Woman searching for specialized healthcare', 'Man looking for tailored clothing'.")

    market_role: Optional[str] = Field(None, description="The user's specific role within the market ecosystem. E.g., 'End-User/Consumer', 'B2B Procurement Manager', 'Wholesale Distributor', 'Industry Journalist', 'Potential Investor'.")

    specific_need: Optional[str] = Field(None, description="The very specific, granular problem or requirement the user has. E.g., 'Needs a laptop with >16 hours of battery life', 'Looking for a CRM that integrates with QuickBooks', 'Requires a gluten-free version of a product'.")

    knowledge_level: Optional[str] = Field(None, description="The user's level of expertise in the relevant topic or industry. E.g., 'Novice/Beginner' (knows nothing), 'Intermediate' (has some experience), 'Expert' (is a professional in the field).")

    language: str = Field("English", description="The primary language the user is thinking and searching in. E.g., 'English', 'Turkish', 'Spanish', 'Mandarin Chinese'.")

    sentiment_bias: Optional[str] = Field(None, description="The user's pre-existing emotional leaning or bias before they even start searching. E.g., 'Brand Loyalist' (loves the brand), 'Skeptical Buyer' (distrusts marketing), 'Price-Conscious Shopper' (hunts for deals), 'Frustrated with a Competitor' (actively looking to switch).")

    query_type: Optional[str] = Field(None, description="The specific type of information the user is looking for in their query. E.g., 'Navigational' (to find a specific website), 'Informational' (to learn something), 'Transactional' (to complete a purchase), 'Commercial Investigation' (to compare options before buying).")

class Prompt(BaseModel):
    perspective: Perspective
    text: str = Field(description="The actual prompt text that would be used to query an AI search engine")

class Response(BaseModel):
    prompt: Prompt
    response: str

class Perspectives(BaseModel):
    perspectives: List[Perspective] = Field(
        description="List of diverse perspectives for assessing brand visibility"
    )

class Prompts(BaseModel):
    prompts: List[Prompt] = Field(
        description="List of prompts generated for a given perspective"
    )

class Competitor(BaseModel):
    name: str
    description: str
    website: str
    logo: str
    industry: str
    location: str
    mentions: int = 0

class Competitors(BaseModel):
    competitors: List[Competitor] = Field(
        description="List of competitors of the brand"
    )

class State(BaseModel):
    brand_info: BrandInfo
    brand_description: Optional[str] = None
    perspectives: List[Perspective] = []
    current_perspective: Optional[Perspective] = None
    prompts: Annotated[List[Prompt], operator.add] = []  # For Send() API
    responses: Annotated[List[Response], operator.add] = [] # For Send() API
    messages: List[BaseMessage] = []
    human_feedback: Optional[Any] = None
    number_of_perspectives: int = 5
    number_of_prompts: int = 5
    number_of_responses: int = 1
    brand_mentions: int = 0
    competitors: List[Competitor] = []