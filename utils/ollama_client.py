"""All HTTP calls to the Ollama API.

This module handles all communication with the Ollama API, including
image-based vision queries and text-only generation requests.
"""

import base64
import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration constants
OLLAMA_HOST: str = os.getenv("GB10_IP", "localhost")
OLLAMA_PORT: str = os.getenv("OLLAMA_PORT", "11434")
MODEL: str = os.getenv("MODEL", "llava:13b")
BASE_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# API endpoints
API_GENERATE_ENDPOINT: str = "/api/generate"
API_CHAT_ENDPOINT: str = "/api/chat"  # TODO: Support chat API for better vision models

# Timeout constants (in seconds)
VISION_TIMEOUT: int = 60
TEXT_TIMEOUT: int = 120


def _image_to_base64(image_path: str | Path) -> str:
    """Read an image file and return its base64-encoded string.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64-encoded image string.

    Raises:
        FileNotFoundError: If the image file does not exist.
        IOError: If the image file cannot be read.

    TODO:
        - Add image format validation (only allow JPG, PNG, JPEG)
        - Add image size validation (max file size limit)
        - Add image dimension validation (min/max width/height)
        - Support PIL Image objects directly
        - Add compression for large images
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    # TODO: Add try-except for read_bytes() to handle permission errors
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def chat_with_image(image_path: str | Path, prompt: str) -> str:
    """Send an image and text prompt to Ollama vision model.

    This function sends an image along with a text prompt to the Ollama
    API using the vision model specified in the MODEL environment variable.

    Args:
        image_path: Path to the image file to analyze.
        prompt: Text prompt describing what to extract from the image.

    Returns:
        The model's response text, stripped of leading/trailing whitespace.

    Raises:
        FileNotFoundError: If the image file does not exist.
        requests.RequestException: If the API request fails.
        ValueError: If the API response is invalid.

    TODO:
        - Add retry logic with exponential backoff
        - Add request/response logging
        - Support streaming responses for better UX
        - Add response caching to avoid duplicate API calls
        - Validate prompt length (max tokens)
        - Add support for multiple images in one request
        - Implement proper error handling with custom exceptions
        - Add request timeout configuration
        - Support different vision models dynamically
        - Add progress callbacks for long-running requests
    """
    b64_image = _image_to_base64(image_path)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [b64_image],
        "stream": False,
    }
    # TODO: Add request validation before sending
    try:
        response = requests.post(
            f"{BASE_URL}{API_GENERATE_ENDPOINT}",
            json=payload,
            timeout=VISION_TIMEOUT,
        )
        response.raise_for_status()
        # TODO: Validate response structure
        result = response.json()
        if "response" not in result:
            raise ValueError("Invalid API response: missing 'response' field")
        return result.get("response", "").strip()
    except requests.Timeout:
        # TODO: Create custom exception classes
        raise requests.RequestException(
            f"Request timeout after {VISION_TIMEOUT}s"
        )
    except requests.RequestException as e:
        # TODO: Add more specific error messages
        raise requests.RequestException(f"API request failed: {e}")


def chat_text_only(prompt: str) -> str:
    """Send a text-only prompt to Ollama and return the response.

    This function sends a text prompt to the Ollama API for text generation
    tasks such as recipe generation.

    Args:
        prompt: Text prompt for the model.

    Returns:
        The model's response text, stripped of leading/trailing whitespace.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the API response is invalid.

    TODO:
        - Add retry logic with exponential backoff
        - Add request/response logging
        - Support streaming responses for better UX
        - Add response caching based on prompt hash
        - Validate prompt length (max tokens)
        - Implement proper error handling with custom exceptions
        - Add request timeout configuration
        - Support different models dynamically
        - Add progress callbacks for long-running requests
        - Add prompt templating system
        - Support system prompts and conversation context
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }
    # TODO: Add request validation before sending
    try:
        response = requests.post(
            f"{BASE_URL}{API_GENERATE_ENDPOINT}",
            json=payload,
            timeout=TEXT_TIMEOUT,
        )
        response.raise_for_status()
        # TODO: Validate response structure
        result = response.json()
        if "response" not in result:
            raise ValueError("Invalid API response: missing 'response' field")
        return result.get("response", "").strip()
    except requests.Timeout:
        # TODO: Create custom exception classes
        raise requests.RequestException(
            f"Request timeout after {TEXT_TIMEOUT}s"
        )
    except requests.RequestException as e:
        # TODO: Add more specific error messages
        raise requests.RequestException(f"API request failed: {e}")


def check_ollama_connection() -> bool:
    """Check if Ollama server is accessible.

    Returns:
        True if Ollama server is reachable, False otherwise.

    TODO:
        - Implement this function to ping Ollama health endpoint
        - Add connection retry logic
        - Cache connection status
        - Return detailed connection info (version, model availability)
    """
    # TODO: Implement health check
    # Example: requests.get(f"{BASE_URL}/api/tags")
    return True


def list_available_models() -> list[str]:
    """List all available models on the Ollama server.

    Returns:
        List of available model names.

    TODO:
        - Implement this function to query Ollama API
        - Cache model list
        - Add model metadata (size, capabilities)
    """
    # TODO: Implement model listing
    # Example: requests.get(f"{BASE_URL}/api/tags")
    return []
