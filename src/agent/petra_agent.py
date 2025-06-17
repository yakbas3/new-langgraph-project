from agent.schema import State
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from agent.nodes import *

# --- Graph Construction ---
builder = StateGraph(State)

# Add nodes
builder.add_node("search_brand_info", search_brand_info)
builder.add_node("synthesize_brand_description", synthesize_brand_description)
builder.add_node("generate_perspectives", generate_perspectives)
builder.add_node("generate_prompts_for_perspective", generate_prompts_for_perspective)
builder.add_node("execute_prompts", execute_prompts)
builder.add_node("count_brand_mentions", count_brand_mentions)
builder.add_node("find_competitors", find_competitors)

# Add edges
builder.add_edge(START, "search_brand_info")
builder.add_edge("search_brand_info", "synthesize_brand_description")
builder.add_edge("synthesize_brand_description", "find_competitors")
builder.add_edge("find_competitors", "generate_perspectives")
builder.add_conditional_edges(
    "generate_perspectives",
    parallel_prompt_generation,
    ["generate_prompts_for_perspective"]
)
builder.add_conditional_edges(
    "generate_prompts_for_perspective",
    execute_prompts_in_parallel,
    ["execute_prompts"]
)
builder.add_edge("execute_prompts", "count_brand_mentions")
builder.add_edge("count_brand_mentions", END)

# Compile the graph
graph = builder.compile(checkpointer=SqliteSaver.from_conn_string("sqlite:///petra_agent.db"))