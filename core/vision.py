"""Image → ingredient list logic.

This module handles the conversion of images to ingredient lists using
the Ollama vision API through the ollama_client module.
"""

from pathlib import Path
from typing import Optional


# Prompt template for ingredient extraction
INGREDIENT_PROMPT: str = (
    "Look at this image of food or ingredients. "
    "List every ingredient you can identify, one per line. "
    "Return only the list, no other text."
)


def image_to_ingredients(image_path: str | Path) -> list[str]:
    """Extract a list of ingredients from a photo.

    This function takes an image path (e.g., photo of fridge or counter)
    and uses vision AI to identify and extract all visible ingredients.

    Args:
        image_path: Path to the image file containing ingredients.

    Returns:
        List of ingredient names as strings. Empty list if no ingredients
        detected or if extraction fails.

    Raises:
        FileNotFoundError: If the image file does not exist.
        requests.RequestException: If the API request fails.

    TODO:
        - Add input validation (file format, size, dimensions)
        - Improve prompt engineering for better accuracy
        - Add ingredient normalization (e.g., "tomatoes" vs "tomato")
        - Filter out non-food items detected
        - Add confidence scores for each ingredient
        - Support multiple images in one call
        - Add ingredient categorization (vegetables, proteins, etc.)
        - Implement ingredient deduplication
        - Add language support for ingredient names
        - Cache results for same image (hash-based)
        - Add progress tracking for long operations
        - Handle partial ingredient names or ambiguous detections
        - Add support for dietary restrictions filtering
    """
    # TODO: Add input validation
    # - Check file exists
    # - Check file format
    # - Check file size
    # - Check image dimensions

    try:
        response = chat_with_image(image_path, INGREDIENT_PROMPT)
    except Exception as e:
        # TODO: Implement proper error handling and logging
        # TODO: Return empty list or raise custom exception?
        return []

    # Parse response into ingredient list
    # TODO: Improve parsing logic to handle various response formats
    lines = [
        line.strip()
        for line in response.strip().splitlines()
        if line.strip()
    ]

    # TODO: Normalize ingredient names
    # - Remove common prefixes ("fresh", "organic", etc.)
    # - Standardize plural/singular forms
    # - Handle typos or variations

    # TODO: Filter out non-ingredients
    # - Remove common false positives
    # - Validate against ingredient database

    return lines


def validate_image(image_path: str | Path) -> tuple[bool, Optional[str]]:
    """Validate that an image file is suitable for processing.

    Args:
        image_path: Path to the image file to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.

    TODO:
        - Implement image validation logic
        - Check file format (JPG, PNG, JPEG only)
        - Check file size (max 10MB?)
        - Check image dimensions (min 100x100, max 4000x4000?)
        - Check image is not corrupted
        - Return detailed error messages
    """
    # TODO: Implement validation
    return True, None


def normalize_ingredient_name(name: str) -> str:
    """Normalize an ingredient name to a standard format.

    Args:
        name: Raw ingredient name from vision model.

    Returns:
        Normalized ingredient name.

    TODO:
        - Remove common prefixes ("fresh", "organic", "raw", etc.)
        - Standardize plural/singular forms
        - Handle common typos
        - Convert to lowercase
        - Remove extra whitespace
        - Handle unit conversions (e.g., "1 cup flour" -> "flour")
    """
    # TODO: Implement normalization
    return name.strip().lower()
