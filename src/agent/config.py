from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Setup LLM and Search Tool ---
model = ChatOpenAI(temperature=0, model="gpt-4o")
search_tool = TavilySearch(max_results=5)