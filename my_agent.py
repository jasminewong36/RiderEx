import asyncio
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from band import Agent
from band.adapters import LangGraphAdapter
from band.config import load_agent_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()

    # Load agent credentials from agent_config.yaml
    agent_id, api_key = load_agent_config("my_agent")

    # Create adapter with LLM and checkpointer
    adapter = LangGraphAdapter(
        llm=ChatOpenAI(
            model="gpt-4o",
            openai_api_key=os.getenv("AIML_API_KEY"),
            openai_api_base=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
        ),
        checkpointer=InMemorySaver(),
    )

    # Create and run the agent
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Agent is running! Press Ctrl+C to stop.")
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
