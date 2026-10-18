"""Trip planner agent

    python -m agent.agent
"""

import logging
import os

from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT
from .tools import get_weather, find_attractions, find_restaurants, find_events, get_transit_info
from uuid import uuid4

load_dotenv()

# silence a noisy advisory warning from the Google SDK
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

# Fail fast and legibly: a placeholder left over from example.env otherwise
# surfaces as a 400 INVALID_ARGUMENT deep inside the first model call.
for _name in ("GOOGLE_API_KEY", "TAVILY_API_KEY"):
    if os.getenv(_name, "").startswith("your_"):
        raise SystemExit(
            f"{_name} in your .env is still the placeholder from example.env. "
            "Replace it with your real key, in .env at your project root."
        )

from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

TOOLS = [get_weather, find_attractions, find_restaurants, find_events, get_transit_info]
SYSTEM_PROMPT = SYSTEM_PROMPT

# You must use an API model for online deployment. Otherwise, we cannot test it properly.
# Options: Gemini, OpenRouter, NVIDIA as posted on Piazza
model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# Local alternative for testing during development
# from langchain_ollama import ChatOllama
# model = ChatOllama(model="qwen3.5:4b", reasoning=False)

trip_agent = create_agent(
    model,
    tools=TOOLS, 
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)


def ask(text: str, thread: str) -> dict:
    """One turn of the conversation. The same thread keeps the memory."""
    config = {"configurable": {"thread_id": thread}}

    try:
        response = trip_agent.invoke(
            {"messages": [HumanMessage(content=text)]}, config
        )
        return {"messages": response["messages"]}
    except Exception as e:
        logging.error(f"Error in ask function: {e}")
        return {"messages": [AIMessage(content="Sorry, I encountered an error. Please try again.")]}

if __name__ == "__main__":
    from .itinerary import build_itinerary

    print("Trip planner. Describe your trip, refine it, then type 'quit'.")
    result = None
    while True:
        user = input("You: ")
        if user.lower() in {"quit", "exit"}:
            break
        result = ask(user, "cli-demo")
        print("Agent:", result["messages"][-1].text)

    if result is not None:
        print("\n--- itinerary ---")
        print(build_itinerary(model, result).model_dump_json(indent=2))
