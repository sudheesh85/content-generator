import os
from typing import Any
from agent_framework.openai import OpenAIChatClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
import asyncio
import logging

logger = logging.getLogger(__name__)

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

    @retry(
        stop=stop_after_attempt(3),  # Retry up to 3 times
        wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff: 2s, 4s, 8s
        retry=retry_if_exception_type((Exception,)),  # Retry on any exception
        reraise=True  # Re-raise the exception after all retries are exhausted
    )
    async def _get_completion(self, prompt: str) -> str:
        """
        Send message to the agent and get response with retry logic.
        
        This method wraps the LLM call with retry logic to handle transient failures:
        - Retries up to 3 times on failure
        - Uses exponential backoff (2s, 4s, 8s)
        - Logs retry attempts for observability
        """
        try:
            # Send message to the agent and get response
            result = await self.agent.run(prompt)
            return result.text
        except Exception as e:
            logger.warning(
                f"LLM call failed for {self.name}: {str(e)}. "
                "Retrying with exponential backoff..."
            )
            raise  # Re-raise to trigger retry mechanism
