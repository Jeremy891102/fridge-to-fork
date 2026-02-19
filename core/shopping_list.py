"""
Inventory + desired dish → strict shopping list logic.

This module handles generating a strict, export-ready shopping list
based on the user's current inventory and an intended dish/recipe idea,
using the Ollama text generation API.

Key property: The model MUST output strict JSON only (no markdown, no prose),
so the UI can parse deterministically and export to CSV/TXT.
"""

from __future__ import annotations

from typing import Optional, Any
from utils.ollama_client import generate_text as chat_text_only
from utils.ollama_client import generate_text_stream

import json
import re


# -----------------------------
# Prompt template (STRICT JSON)
# -----------------------------

SHOPPING_LIST_PROMPT_TEMPLATE = r"""
You are an inventory-aware home cooking assistant.

You are given:
1) The user's current inventory ingredients (free-text).
2) The user's request for a dish/meal/recipe idea.

Your task:
Return a STRICT JSON object describing what the user should buy to cook the requested dish.

Hard rules:
- Output MUST be valid JSON and NOTHING ELSE (no markdown, no commentary).
- Use double quotes for all keys/strings.
- Do not wrap JSON in code fences.
- Do not include trailing commas.
- If you are unsure about a quantity, set "quantity" to null and still include "unit" if known.
- Prefer minimal, practical shopping lists for a normal home cook.
- Assume common pantry staples are available unless the dish strongly depends on them:
  salt, black pepper, neutral oil, sugar, flour, water.
- IMPORTANT: Compare against inventory. Items already in inventory MUST go to "already_have", not "missing_items".

Inventory:
{inv}

User request:
{user_message}

Return JSON with EXACTLY this schema:

{{
  "dish": string,
  "missing_items": [
    {{
      "name": string,
      "quantity": number|null,
      "unit": string|null,
      "category": string,
      "priority": "must"|"nice_to_have",
      "substitutions": [string]
    }}
  ],
  "optional_items": [
    {{
      "name": string,
      "quantity": number|null,
      "unit": string|null,
      "category": string,
      "priority": "must"|"nice_to_have",
      "substitutions": [string]
    }}
  ],
  "already_have": [string],
  "notes": [string]
}}

Category guidelines (pick one):
- "produce", "meat/seafood", "dairy/eggs", "dry goods", "condiments/spices", "frozen", "bakery", "other"

Now output the JSON only.
"""


# -----------------------------
# Public API (chat-style)
# -----------------------------

def generate_shopping_list_json(
    user_message: str,
    inventory: list[str],
    history: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """
    Generate a strict JSON shopping list. Returns a parsed dict.

    Args:
        user_message: e.g. "I want to cook mapo tofu tonight"
        inventory: list of ingredient strings
        history: optional conversation history; not strictly required for shopping list

    Returns:
        A dict parsed from model output JSON.

    Raises:
        ValueError: if inputs are empty or JSON is invalid after retries.
    """
    if not user_message or not user_message.strip():
        raise ValueError("user_message cannot be empty")
    if inventory is None:
        inventory = []

    inv = _format_list(_dedupe_normalized(inventory))

    # Keep history minimal; optional for shopping list.
    history_txt = ""
    if history:
        history_txt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-4:]
        ).strip()

        # If you want: incorporate history into user_message (but keep schema strict)
        if history_txt:
            user_message = f"{user_message}\n\nConversation context:\n{history_txt}"

    prompt = SHOPPING_LIST_PROMPT_TEMPLATE.format(
        inv=inv,
        user_message=user_message.strip(),
    )

    raw = (chat_text_only(prompt) or "").strip()
    data = _parse_strict_json(raw)

    ok, msg = validate_shopping_list(data, inventory=inventory)
    if not ok:
        # One retry with a correction prompt (still strict JSON-only)
        correction_prompt = _build_correction_prompt(
            inventory=inv,
            user_message=user_message,
            bad_output=raw,
            validation_error=msg,
        )
        raw2 = (chat_text_only(correction_prompt) or "").strip()
        data2 = _parse_strict_json(raw2)
        ok2, msg2 = validate_shopping_list(data2, inventory=inventory)
        if not ok2:
            raise ValueError(f"Invalid shopping list JSON after retry: {msg2}")
        return data2

    return data


def stream_shopping_list_json_text(
    user_message: str,
    inventory: list[str],
    history: Optional[list[dict]] = None,
):
    """
    Stream STRICT JSON text tokens as generated.
    UI can collect full text then json.loads.

    Note: streaming cannot be validated until completion.
    """
    if not user_message or not user_message.strip():
        raise ValueError("user_message cannot be empty")
    if inventory is None:
        inventory = []

    inv = _format_list(_dedupe_normalized(inventory))

    history_txt = ""
    if history:
        history_txt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-4:]
        ).strip()
        if history_txt:
            user_message = f"{user_message}\n\nConversation context:\n{history_txt}"

    prompt = SHOPPING_LIST_PROMPT_TEMPLATE.format(
        inv=inv,
        user_message=user_message.strip(),
    )
    return generate_text_stream(prompt)


# -----------------------------
# Validation & parsing
# -----------------------------

def _parse_strict_json(text: str) -> dict[str, Any]:
    """
    Parse strict JSON. If the model accidentally adds leading/trailing noise,
    attempt a conservative extraction of the first JSON object.
    """
    if not text:
        raise ValueError("Empty model output; expected JSON")

    # First try direct parse
    try:
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ValueError("Top-level JSON must be an object")
        return obj
    except json.JSONDecodeError:
        pass

    # Conservative extraction: find first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output is not JSON (no object braces found)")

    candidate = text[start : end + 1].strip()
    obj = json.loads(candidate)
    if not isinstance(obj, dict):
        raise ValueError("Top-level JSON must be an object")
    return obj


def validate_shopping_list(
    data: dict[str, Any],
    inventory: list[str],
) -> tuple[bool, str]:
    """
    Validate schema + basic inventory consistency.

    Rules:
    - Must contain exact top-level keys.
    - missing_items/optional_items entries must have required fields.
    - already_have should not be empty if overlap exists.
    - Items in missing_items should NOT be already in inventory (best-effort string match).
    """
    required_top_keys = {"dish", "missing_items", "optional_items", "already_have", "notes"}
    if set(data.keys()) != required_top_keys:
        return False, f"Top-level keys must be exactly {sorted(required_top_keys)}"

    if not isinstance(data["dish"], str) or not data["dish"].strip():
        return False, '"dish" must be a non-empty string'

    if not isinstance(data["missing_items"], list):
        return False, '"missing_items" must be a list'
    if not isinstance(data["optional_items"], list):
        return False, '"optional_items" must be a list'
    if not isinstance(data["already_have"], list):
        return False, '"already_have" must be a list'
    if not isinstance(data["notes"], list):
        return False, '"notes" must be a list'

    inv_norm = set(_dedupe_normalized(inventory))

    for k in ["missing_items", "optional_items"]:
        for i, item in enumerate(data[k]):
            ok, msg = _validate_item(item, path=f"{k}[{i}]")
            if not ok:
                return False, msg

            # Best-effort check: missing item name shouldn't be in inventory
            name_norm = _normalize_ingredient(item.get("name", ""))
            if k == "missing_items" and name_norm in inv_norm:
                return False, f'{k}[{i}].name "{item.get("name")}" is already in inventory; move it to "already_have"'

    # already_have should be strings
    for i, s in enumerate(data["already_have"]):
        if not isinstance(s, str):
            return False, f'already_have[{i}] must be a string'

    # notes should be strings
    for i, s in enumerate(data["notes"]):
        if not isinstance(s, str):
            return False, f'notes[{i}] must be a string'

    return True, "ok"


def _validate_item(item: Any, path: str) -> tuple[bool, str]:
    if not isinstance(item, dict):
        return False, f"{path} must be an object"

    required = {"name", "quantity", "unit", "category", "priority", "substitutions"}
    if set(item.keys()) != required:
        return False, f"{path} keys must be exactly {sorted(required)}"

    if not isinstance(item["name"], str) or not item["name"].strip():
        return False, f'{path}.name must be a non-empty string'

    if item["quantity"] is not None and not isinstance(item["quantity"], (int, float)):
        return False, f'{path}.quantity must be a number or null'

    if item["unit"] is not None and not isinstance(item["unit"], str):
        return False, f'{path}.unit must be a string or null'

    if not isinstance(item["category"], str) or not item["category"].strip():
        return False, f'{path}.category must be a non-empty string'

    if item["priority"] not in ("must", "nice_to_have"):
        return False, f'{path}.priority must be "must" or "nice_to_have"'

    if not isinstance(item["substitutions"], list) or any(not isinstance(x, str) for x in item["substitutions"]):
        return False, f'{path}.substitutions must be a list of strings'

    return True, "ok"


# -----------------------------
# Helpers (normalize/format)
# -----------------------------

def _normalize_ingredient(s: str) -> str:
    """Light normalization to stabilize matching."""
    s = (s or "").strip().lower()
    s = re.sub(r"^[-*•\d\.\)\s]+", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _dedupe_normalized(items: list[str]) -> list[str]:
    normed: list[str] = []
    seen = set()
    for x in items:
        n = _normalize_ingredient(x)
        if not n:
            continue
        if n not in seen:
            seen.add(n)
            normed.append(n)
    return normed


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


# -----------------------------
# Retry prompt (correction)
# -----------------------------

def _build_correction_prompt(
    inventory: str,
    user_message: str,
    bad_output: str,
    validation_error: str,
) -> str:
    return rf"""
You must output STRICT JSON only.

Inventory:
{inventory}

User request:
{user_message}

Your previous output was invalid.
Validation error:
{validation_error}

Invalid output (do not repeat it):
{bad_output}

Now regenerate the shopping list following the EXACT schema below.
Output JSON only; no markdown; no extra text.

{{
  "dish": string,
  "missing_items": [
    {{
      "name": string,
      "quantity": number|null,
      "unit": string|null,
      "category": string,
      "priority": "must"|"nice_to_have",
      "substitutions": [string]
    }}
  ],
  "optional_items": [
    {{
      "name": string,
      "quantity": number|null,
      "unit": string|null,
      "category": string,
      "priority": "must"|"nice_to_have",
      "substitutions": [string]
    }}
  ],
  "already_have": [string],
  "notes": [string]
}}
"""
