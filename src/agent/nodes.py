from langchain_core.messages import HumanMessage, AIMessage
from agent.schema import Response, Perspectives, Prompts, State, Competitors
from agent.config import model, search_tool
from langgraph.constants import Send
from typing import List
from agent.prompts.generate_perspectives import generate_perspectives_system_message
from agent.prompts.generate_prompts import generate_prompts_system_message

# --- Workflow Node Implementations ---
def search_brand_info(state: State) -> State:
    company_name = state.brand_info.company_name
    website = state.brand_info.website
    query = f"What is {company_name} ({website})? Give a comprehensive overview of the brand, its products, market, and recent activities."
    search_results = search_tool.invoke({"query": query})
    state.brand_description = str(search_results)
    state.messages.append(HumanMessage(content=f"Tavily search results for {company_name}: {search_results}"))
    return state

def synthesize_brand_description(state: State) -> State:
    company_name = state.brand_info.company_name
    website = state.brand_info.website
    search_context = state.brand_description or ""
    prompt = f"""
Given the following search results about the brand {company_name} (website: {website}), write a comprehensive, objective, and up-to-date description of the brand, its core business, products, market position, and any recent news or activities. Be as detailed as possible for an AI agent to understand the brand's domain and context.\n\nSearch Results:\n{search_context}
"""
    messages = [HumanMessage(content=prompt)]
    ai_message: AIMessage = model.invoke(messages)
    if isinstance(ai_message.content, list):
        description = "\n".join(str(x) for x in ai_message.content)
    else:
        description = str(ai_message.content)
    state.brand_description = description
    state.messages.append(ai_message)
    return state

def find_competitors(state: State) -> State:
    brand_description = state.brand_description or ""
    prompt = f"""
Given the following brand description, find the top 10 competitors of the brand :
{brand_description}
"""
    structured_llm = model.with_structured_output(Competitors)
    competitors = structured_llm.invoke([HumanMessage(content=prompt)])
    state.competitors = competitors.competitors

    return state

def generate_perspectives(state: State) -> State:
    brand_description = state.brand_description or ""
    number_of_perspectives = state.number_of_perspectives
    region = state.brand_info.region
    language = state.brand_info.language

    system_message = generate_perspectives_system_message(number_of_perspectives, region, language)
    
    human_message = HumanMessage(content=f"Generate perspectives based on this brand description:\n{brand_description}")
    
    # Use structured output for Perspectives
    structured_llm = model.with_structured_output(Perspectives)
    result = structured_llm.invoke([system_message, human_message])
    
    state.perspectives = result.perspectives
    state.messages.append(AIMessage(content=f"Generated {len(result.perspectives)} perspectives"))
    return state

def human_feedback_node(state: State) -> State:
    return state

def human_feedback_node2(state: State) -> State:
    return state

def generate_prompts_for_perspective(state: dict) -> dict:
    """Receives a dictionary payload from Send() and generates prompts."""
    # Use dictionary key access instead of attribute access
    brand_description = state.get("brand_description", "")
    perspective = state.get("current_perspective")
    number_of_prompts = state.get("number_of_prompts", 5)
    region = state.get("region", "United States")
    language = state.get("language", "English")

    if not perspective:
        return {"prompts": []} # Return a valid update, even if empty

    system_message = generate_prompts_system_message(number_of_prompts, region, language)

    human_message = HumanMessage(content=f"""Generate prompts for this perspective:
{perspective.model_dump_json(indent=2)}

Brand Description:
{brand_description}""")

    # Use structured output for Prompts
    structured_llm = model.with_structured_output(Prompts)
    result = structured_llm.invoke([system_message, human_message])

    # Wrap the list in a dictionary with the key matching the State field
    return {"prompts": result.prompts}

def parallel_prompt_generation(state: State) -> str | List[Send]:
    """
    Route based on human feedback. If feedback is provided, return to perspective generation.
    Otherwise, initiate parallel prompt generation using Send().
    """
    return [
        Send("generate_prompts_for_perspective", {"current_perspective": perspective, "brand_description": state.brand_description, "number_of_prompts": state.number_of_prompts})
        for perspective in state.perspectives
    ]

def execute_prompts_in_parallel(state: State) -> List[Send]:
    """
    Executes all generated prompts against the LLM and collects the responses.
    This node runs after all parallel prompt generation is complete.
    """
    print(f"--- Executing {len(state.prompts)} generated prompts ---")
    
    # Create a list of Send() calls for each prompt
    return [
        Send("execute_prompts", {"prompt": prompt})
        for prompt in state.prompts
    ]

def execute_prompts(payload: dict) -> dict:
    """
    Executes a SINGLE prompt against the LLM.
    This node is the worker that runs in parallel.
    """
    # 1. Get the single prompt from the payload dictionary.
    p = payload.get("prompt")
    if not p:
        # Return an empty list for the update if the prompt is missing
        return {"responses": []}

    # 2. Invoke the model with the text from the single prompt.
    ai_message: AIMessage = model.invoke(p.text)

    # Ensure the response content is a string.
    if isinstance(ai_message.content, list):
        response_text = "\n".join(str(x) for x in ai_message.content)
    else:
        response_text = str(ai_message.content)

    # 3. Create a single Response object.
    result = Response(prompt=p, response=response_text)

    # 4. Return a dictionary to update the 'responses' field.
    #    It MUST be a list because the state reducer (operator.add) concatenates lists.
    return {"responses": [result]}

def count_brand_mentions(state: State) -> State:
    """
    Counts brand and competitor mentions across all responses.
    """
    responses = state.responses
    brand_name = state.brand_info.company_name
    competitors = state.competitors

    # Initialize counts if they don't exist, or reset for this run
    state.brand_mentions = 0

    # Count brand mentions
    for response in responses:
        if brand_name.lower() in response.response.lower(): # Case-insensitive check
            state.brand_mentions += 1

    # Count competitor mentions
    for competitor in competitors:

        for response in responses:
            if competitor.name.lower() in response.response.lower(): # Case-insensitive check
                competitor.mentions += 1
    
    return state