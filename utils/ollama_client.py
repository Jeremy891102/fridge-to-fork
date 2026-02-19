"""Ollama API client for Fridge-to-Fork hackathon app.

Loads GB10_IP, OLLAMA_PORT, MODEL from .env and provides health check,
vision (image + prompt), and text-only generation against the Ollama API.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

# From .env
GB10_IP: str = os.getenv("GB10_IP", "localhost")
OLLAMA_PORT: str = os.getenv("OLLAMA_PORT", "11434")
MODEL: str = os.getenv("MODEL", "llava:13b")
CHAT_MODEL: str = os.getenv("CHAT_MODEL", "llama3:8b")

BASE_URL: str = f"http://{GB10_IP}:{OLLAMA_PORT}"


def health_check() -> bool:
    """Check if the Ollama server is reachable.

    Sends a GET request to BASE_URL with a 3-second timeout.
    Called by: app startup, UI status indicators, or tests.

    Returns:
        True if the server responds with status_code 200, False on any exception.
    """
    try:
        resp = requests.get(BASE_URL, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def generate_with_image(prompt: str, image_base64: str) -> str:
    """Generate a response from the vision model given a prompt and a base64 image.

    POSTs to {BASE_URL}/api/generate with model, prompt, images=[image_base64],
    and stream=False. Called by: core/vision or app when detecting ingredients from a photo.

    Args:
        prompt: Text prompt for the vision model.
        image_base64: Base64-encoded image string.

    Returns:
        The model response text from resp.json()["response"].

    Raises:
        Exception: With message "Vision API failed: {e}" on any request or parse error.
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "keep_alive": -1,
                "options": {"temperature": 0},
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        raise Exception(f"Vision API failed: {e}") from e


def generate_text(prompt: str) -> str:
    """Generate a text-only response from the model.

    POSTs to {BASE_URL}/api/generate with model, prompt, and stream=False.
    Called by: core/recipe or app when generating a recipe from ingredients.

    Args:
        prompt: Text prompt for the model.

    Returns:
        The model response text from resp.json()["response"].

    Raises:
        Exception: With message "Text API failed: {e}" on any request or parse error.
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": -1,
                "options": {"temperature": 0.3},
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        raise Exception(f"Text API failed: {e}") from e


def generate_text_stream(prompt: str):
    """Yield response tokens from the model as they are generated.

    Uses stream=True on the Ollama API and yields each token string
    as it arrives. Called by: core/recipe when streaming chef responses.

    Args:
        prompt: Text prompt for the model.

    Yields:
        Individual token strings from the model response.

    Raises:
        Exception: With message "Text stream API failed: {e}" on error.
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": True,
                "keep_alive": -1,
                "options": {"temperature": 0.3},
            },
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
    except Exception as e:
        raise Exception(f"Text stream API failed: {e}") from e


def generate_chat_stream(messages: list[dict]):
    """Yield response tokens using the /api/chat endpoint with role-separated messages.

    Uses Ollama's chat API which properly handles system/user/assistant turn
    separation, giving significantly better instruction-following than a flat
    prompt string. Each message dict must have "role" and "content" keys.

    Args:
        messages: List of {"role": "system"|"user"|"assistant", "content": str}.

    Yields:
        Individual token strings from the assistant response.

    Raises:
        Exception: With message "Chat stream API failed: {e}" on error.
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": messages,
                "stream": True,
                "keep_alive": -1,
                "options": {"temperature": 0.3},
            },
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
    except Exception as e:
        raise Exception(f"Chat stream API failed: {e}") from e


if __name__ == "__main__":
    print("Health check:", health_check())
    print("Text test:", generate_text("say hello in one word"))
