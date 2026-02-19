"""YOLO World inference service for GB10.

Run on Dell GB10: uvicorn yolo_service:app --host 0.0.0.0 --port 8001
Uses Fridge Ontology (data/fridge_ontology.json) for visual prompts; returns canonical labels.
"""

import base64
import io
import json
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel

app = FastAPI(title="Fridge-to-Fork YOLO Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fallback if ontology is missing
DEFAULT_CLASSES = [
    "egg", "milk", "cheese", "tomato", "onion", "garlic", "carrot", "potato",
    "apple", "banana", "orange", "lemon", "bread", "butter", "chicken", "beef",
    "fish", "rice", "pasta", "flour", "sugar", "salt", "pepper", "oil",
    "yogurt", "lettuce", "cucumber", "bell pepper", "broccoli", "mushroom",
    "bacon", "sausage", "ham", "avocado", "strawberry", "grape", "watermelon",
    "cabbage", "spinach", "celery", "corn", "pea", "bean", "lime", "kiwi",
]

_ontology_path = Path(__file__).resolve().parent / "data" / "fridge_ontology.json"
_model = None
_alias_to_canonical = None
_prompt_list = None


# Put these canonicals first so their prompts are at the front of the class list (better recall for common fridge veggies).
PRIORITY_CANONICALS = [
    "carrot", "cabbage", "cucumber", "red_chili_pepper", "cauliflower",
    "broccoli", "bell_pepper", "eggplant", "pea", "blueberry", "tomato", "onion",
]


def _load_ontology():
    """Load fridge_ontology.json: canonical -> [aliases]. Build alias->canonical and flat prompt list.
    Priority canonicals are added first so the model sees them earlier."""
    global _alias_to_canonical, _prompt_list
    if _alias_to_canonical is not None:
        return
    _alias_to_canonical = {}
    _prompt_list = []
    if _ontology_path.exists():
        try:
            data = json.loads(_ontology_path.read_text(encoding="utf-8"))
            ordered_keys = [k for k in PRIORITY_CANONICALS if k in data]
            ordered_keys += [k for k in data if k not in ordered_keys]
            for canonical in ordered_keys:
                aliases = data[canonical]
                for alias in aliases:
                    a = str(alias).strip()
                    if a and a not in _alias_to_canonical:
                        _alias_to_canonical[a] = canonical
                        _prompt_list.append(a)
        except Exception:
            pass
    if not _prompt_list:
        _prompt_list = list(DEFAULT_CLASSES)
        _alias_to_canonical = {c: c for c in DEFAULT_CLASSES}


def get_model():
    global _model
    _load_ontology()
    if _model is None:
        try:
            from ultralytics import YOLO
            model_id = os.getenv("YOLO_MODEL", "yolov8s-worldv2.pt")
            _model = YOLO(model_id)
            _model.set_classes(_prompt_list)
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}") from e
    return _model


class DetectRequest(BaseModel):
    image_base64: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "yolo-world"}


@app.get("/status")
def status():
    """Report whether YOLO model weights are loaded (loads on first call)."""
    try:
        model = get_model()
        model_id = getattr(model, "model", None)
        model_name = getattr(model_id, "names", None) if model_id is not None else None
        return {
            "status": "ok",
            "service": "yolo-world",
            "model_loaded": True,
            "model_id": os.getenv("YOLO_MODEL", "yolov8s-worldv2.pt"),
            "num_prompts": len(_prompt_list) if _prompt_list else 0,
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "yolo-world",
            "model_loaded": False,
            "error": str(e),
        }


@app.post("/detect")
def detect(body: DetectRequest):
    """Run YOLO-World on image, return list of detected ingredient labels."""
    try:
        raw = base64.b64decode(body.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}")
    try:
        img = Image.open(io.BytesIO(raw))
        arr = np.array(img)
        model = get_model()
        results = model.predict(source=arr, verbose=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _load_ontology()
    labels = []
    seen = set()
    if results and len(results) > 0:
        r = results[0]
        if r.boxes is not None and hasattr(r.boxes, "cls"):
            names = r.names or {}
            for idx in r.boxes.cls.cpu().numpy().astype(int):
                raw = names.get(idx, "")
                if not raw:
                    continue
                canonical = _alias_to_canonical.get(raw, raw)
                if canonical not in seen:
                    seen.add(canonical)
                    labels.append(canonical)
    return {"labels": labels, "ingredients_detected": labels}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("YOLO_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
