"""
FastMCP Server for OpenAI Client
"""

import logging
from fastmcp_http.server import FastMCPHttpServer
import threading
from amp_lib.openai_client import OpenAIClient
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create server
mcp = FastMCPHttpServer(
    "AMPServer",
    description="AMP Server - Interface for interacting with AI services such as chat completion and listing available models.",
)

# Initialize client
client = OpenAIClient(api_key="", base_url="http://127.0.0.1:17173")


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A message in a chat conversation"""

    role: str
    content: str


@mcp.tool()
def chat_completion(
    messages: list[ChatMessage], model: str = "gpt-3.5-turbo", max_tokens: int = 8192
) -> str:
    """Generate a chat completion response
    Args:
        messages: List of ChatMessage objects
        model: Model to use for completion
        max_tokens: Maximum tokens to generate
    """
    try:
        # Convert ChatMessage objects to dictionaries
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        response = client.chat_completion(
            messages=formatted_messages, model=model, max_tokens=max_tokens
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        return f"error: {str(e)}"


@mcp.tool()
def list_models() -> list[str]:
    """Get a list of available models"""
    try:
        return [model.id for model in client.models.list()]
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return []


def start_mcp_server():
    mcp.run_http()


def run_in_thread():
    thread = threading.Thread(target=start_mcp_server, daemon=True)
    thread.start()
    return thread
