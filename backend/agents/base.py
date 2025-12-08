import os
from typing import Any
from agent_framework.openai import OpenAIChatClient

class BaseAgent:
    def __init__(self, name: str, instructions: str = "You are a helpful AI assistant."):
        self.name = name
        # Initialize OpenAIChatClient and create the agent
        client = OpenAIChatClient(model_id="gpt-4o")
        self.agent = client.create_agent(
            instructions=instructions,
            name=name
        )

    async def process(self, input_data: Any) -> Any:
        raise NotImplementedError

    async def _get_completion(self, prompt: str) -> str:
        # Send message to the agent and get response
        result = await self.agent.run(prompt)
        return result.text
