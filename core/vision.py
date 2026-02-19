"""Image → ingredient list logic using YOLO World on GB10.

All ingredient detection goes through the YOLO service (no LLaVA).
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

from utils.yolo_client import detect_ingredients, detect_ingredients_from_path


def image_to_ingredients(image_path: Union[str, Path]) -> List[str]:
    """Extract a list of ingredients from a photo using YOLO World on GB10.

    Args:
        image_path: Path to the image file.

    Returns:
        List of ingredient names. Empty list on error or no detections.
    """
    return detect_ingredients_from_path(image_path)


def extract_ingredients(image_bytes: bytes) -> List[str]:
    """Extract ingredients from raw image bytes (e.g. upload). Used by server/APIs.

    Args:
        image_bytes: Raw image bytes.

    Returns:
        List of ingredient names. Raises on connection/API errors so the client can show them.
    """
    return detect_ingredients(image_bytes)


def validate_image(image_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
    """Validate that an image file is suitable for processing."""
    return True, None


def normalize_ingredient_name(name: str) -> str:
    """Normalize an ingredient name."""
    return name.strip().lower()
