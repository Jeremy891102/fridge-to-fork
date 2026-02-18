"""Utility modules for Fridge-to-Fork.

This package contains utility modules for API communication and other
helper functions.
"""

from utils.ollama_client import (
    generate_text,
    generate_with_image,
    health_check,
)

__all__ = [
    "generate_text",
    "generate_with_image",
    "health_check",
]
