"""Client for GB10 YOLO World inference service.

Sends images to the YOLO service running on GB10 and returns
detected ingredient labels.
"""

import base64
import os
from pathlib import Path
from typing import List, Union

import requests
from dotenv import load_dotenv

load_dotenv()

YOLO_SERVICE_URL: str = os.getenv("YOLO_SERVICE_URL", "http://localhost:8001")
DETECT_ENDPOINT: str = f"{YOLO_SERVICE_URL.rstrip('/')}/detect"
TIMEOUT: int = 60


def detect_ingredients(image_bytes: bytes) -> List[str]:
    """Send image to GB10 YOLO service and return detected ingredient labels.

    Args:
        image_bytes: Raw image bytes (e.g. from UploadFile.read() or Path.read_bytes()).

    Returns:
        List of detected ingredient names (strings). Empty list on error or no detections.

    Raises:
        requests.RequestException: On connection or API error (caller may catch and return []).
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {"image_base64": b64}
    resp = requests.post(DETECT_ENDPOINT, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    labels = data.get("labels") or data.get("ingredients_detected") or []
    return [str(x).strip().lower() for x in labels if x]


def detect_ingredients_from_path(image_path: Union[str, Path]) -> List[str]:
    """Load image from file and run YOLO detection.

    Args:
        image_path: Path to image file.

    Returns:
        List of detected ingredient names.
    """
    path = Path(image_path)
    if not path.exists():
        return []
    return detect_ingredients(path.read_bytes())
