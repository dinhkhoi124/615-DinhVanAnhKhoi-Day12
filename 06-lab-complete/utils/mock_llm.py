"""Small local LLM substitute used by the deployment lab."""
import random
import time


RESPONSES = [
    "The production agent received your question successfully.",
    "This is a mock response. Replace it with an LLM provider in production.",
    "The agent is healthy, authenticated, and ready to scale.",
]


def ask(question: str, delay: float = 0.1) -> str:
    time.sleep(delay)
    return f"{random.choice(RESPONSES)} Question: {question}"
