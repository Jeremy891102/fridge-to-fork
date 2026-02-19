import base64
import hashlib
import json
import re

import streamlit as st
import requests
from PIL import Image
import io
from pathlib import Path
from utils.ollama_client import generate_text

from utils.ollama_client import generate_with_image
# from core.recipe import chat_with_chef
# from core.recipe import ingredients_to_recipe
from core.recipe import stream_chef_response


# ── INVENTORY HELPERS ─────────────────────────────────────────────────────────
INVENTORY_FILE = Path("inventory.json")

def load_inventory() -> list:
    if not INVENTORY_FILE.exists():
        return []
    return json.loads(INVENTORY_FILE.read_text())

def save_inventory(items: list):
    INVENTORY_FILE.write_text(json.dumps(items))

def merge_ingredients(existing: list, new_items: list) -> list:
    combined = {item.lower().strip() for item in existing + new_items}
    return sorted(combined)
# ──────────────────────────────────────────────────────────────────────────────

# ── SHOPPING LIST HELPERS ─────────────────────────────────────────────────────
from core.recipe import extract_recipe_ingredients  # noqa: E402

SHOPPING_LIST_FILE = Path("shopping_list.json")

def load_shopping_list() -> list:
    if not SHOPPING_LIST_FILE.exists():
        return []
    return json.loads(SHOPPING_LIST_FILE.read_text())

def save_shopping_list(items: list):
    SHOPPING_LIST_FILE.write_text(json.dumps(items))

_PANTRY_STAPLES = {
    "salt", "pepper", "black pepper", "white pepper", "oil", "olive oil",
    "vegetable oil", "sugar", "flour", "butter", "water", "garlic", "onion",
    "soy sauce", "vinegar", "baking soda", "baking powder",
}

def get_missing_ingredients(recipe_ings: list[str], inventory: list[str]) -> list[str]:
    inv_set = {item.lower() for item in inventory}
    missing = []
    for ing in recipe_ings:
        ing_lower = ing.lower()
        if any(staple in ing_lower for staple in _PANTRY_STAPLES):
            continue
        if not any(ing_lower in inv_item or inv_item in ing_lower for inv_item in inv_set):
            missing.append(ing)
    return missing
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fridge-to-Fork",
    page_icon="🍳",
    layout="centered",
)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_scan" not in st.session_state:
    st.session_state.pending_scan = None
if "last_scanned_hash" not in st.session_state:
    st.session_state.last_scanned_hash = None
# ── DIETARY RESTRICTIONS session state ────────────────────────────────────────
if "dietary_restrictions" not in st.session_state:
    st.session_state.dietary_restrictions = []
# ──────────────────────────────────────────────────────────────────────────────

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🍳 Fridge-to-Fork")
st.caption("Snap your fridge. Chat with your personal AI chef.")
st.divider()

# ── SECTION 1: INVENTORY ──────────────────────────────────────────────────────
st.subheader("📦 My Fridge Inventory")

inventory = load_inventory()

if not inventory:
    st.info("Your fridge is empty. Scan a photo below to add ingredients.")
else:
    for item in inventory:
        col1, col2 = st.columns([6, 1])
        col1.write(f"• {item}")
        if col2.button("✕", key=f"remove_{item}"):
            inventory.remove(item)
            save_inventory(inventory)
            st.rerun()

    if st.button("🗑️ Clear All"):
        save_inventory([])
        st.rerun()

st.divider()

# ── SECTION 1.5: SHOPPING LIST ───────────────────────────────────────────────
_shopping_list = load_shopping_list()
if _shopping_list:
    st.subheader("🛒 Shopping List")
    for _item in _shopping_list:
        _c1, _c2 = st.columns([6, 1])
        _c1.write(f"• {_item}")
        if _c2.button("✕", key=f"sl_remove_{_item}"):
            _shopping_list.remove(_item)
            save_shopping_list(_shopping_list)
            st.rerun()
    if st.button("🗑️ Clear Shopping List"):
        save_shopping_list([])
        st.rerun()
    st.divider()
# ──────────────────────────────────────────────────────────────────────────────

# ── SECTION 2: SCAN ───────────────────────────────────────────────────────────
st.subheader("📷 Scan New Item")
st.caption(
    "In production, this happens automatically when you put groceries away. "
    "Here it's exposed so you can see the pipeline in action."
)

input_mode = st.radio(
    "Input mode",
    ["📁 Upload a photo", "📷 Use camera"],
    horizontal=True,
    label_visibility="collapsed",
)

image_bytes = None
image = None

if input_mode == "📁 Upload a photo":
    uploaded_file = st.file_uploader(
        "Upload a fridge photo",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(image_bytes))

elif input_mode == "📷 Use camera":
    camera_file = st.camera_input("Point at your open fridge")
    if camera_file is not None:
        image_bytes = camera_file.read()
        image = Image.open(io.BytesIO(image_bytes))

if image is not None:
    st.image(image, caption="Fridge scan", width='stretch')

if image_bytes is not None:
    img_hash = hashlib.md5(image_bytes).hexdigest()
    if img_hash != st.session_state.last_scanned_hash:
        with st.spinner("Scanning ingredients..."):
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            prompt = (
                "You are a food inventory scanner. Look at this fridge image carefully.\n\n"
                "List only the food items you can clearly and confidently identify. "
                "Be conservative — if you are not sure, leave it out.\n\n"
                "Rules:\n"
                "- Output ONLY a JSON array of strings, nothing else\n"
                "- Each string is a single food item (e.g. \"apple\", \"milk\", \"eggs\")\n"
                "- No adjectives, quantities, or descriptions\n"
                "- No packaging, containers, or kitchen tools\n"
                "- No items you are uncertain about\n\n"
                "Example: [\"apple\", \"milk\", \"eggs\", \"cheddar cheese\"]\n\n"
                "JSON array:"
            )
            try:
                raw = generate_with_image(prompt, image_b64)
                # Try JSON parsing first, fall back to comma-split
                new_items = []
                match = re.search(r'\[.*\]', raw, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group())
                        new_items = [
                            str(item).strip().lower()
                            for item in parsed
                            if str(item).strip()
                        ]
                    except json.JSONDecodeError:
                        pass
                if not new_items:
                    # Strip JSON array syntax before splitting
                    cleaned = raw.strip().lstrip("[").rstrip("]")
                    new_items = [
                        item.strip().strip("\"'").lower()
                        for item in cleaned.split(",")
                        if item.strip().strip("\"'")
                    ]
                existing = st.session_state.pending_scan or []
                seen = {i.lower() for i in existing}
                for item in new_items:
                    if item.lower() not in seen:
                        existing.append(item)
                        seen.add(item.lower())
                st.session_state.pending_scan = existing
                st.session_state.last_scanned_hash = img_hash
            except Exception as e:
                st.error(f"Scan failed: {e}")
                st.stop()

if st.session_state.pending_scan is not None:
    st.markdown("**Review detected ingredients — uncheck anything wrong:**")
    checked = {
        item: st.checkbox(item, value=True, key=f"scan_{item}")
        for item in st.session_state.pending_scan
    }
    confirmed = [item for item, selected in checked.items() if selected]

    if st.button("✅ Add to Inventory", type="primary", disabled=not confirmed):
        existing = load_inventory()
        merged = merge_ingredients(existing, confirmed)
        save_inventory(merged)
        st.session_state.pending_scan = None
        st.success(f"✅ {len(confirmed)} ingredients added. Inventory now has {len(merged)} items.")
        st.rerun()

st.divider()

# ── SECTION 3: CHAT ───────────────────────────────────────────────────────────
st.subheader("💬 What Can I Cook?")

current_inventory = load_inventory()


# def build_chat_prompt(user_message: str, inventory: list[str], history: list[dict]) -> str:
#     inv = "\n".join(f"- {x}" for x in inventory)
#
#     recent = history[-6:]
#     history_txt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
#
#     return f"""You are an AI chef assistant.
#
# Rules:
# - Prioritize using the inventory items as primary ingredients.
# - You may add at most 3 pantry staples from: salt, pepper, oil, water, sugar, soy sauce, butter, garlic, onion.
# - If the user asks "what can I cook", propose 2 options max, each with short steps.
# - If the user asks for one recipe, return one detailed recipe with steps.
# - No unnecessary commentary.
#
# Current inventory:
# {inv}
#
# Conversation so far:
# {history_txt}
#
# USER: {user_message}
# ASSISTANT:
# """


if not current_inventory:
    st.warning("Scan some ingredients first — then ask me what to cook.")
else:
    col1, col2 = st.columns([8, 1])
    col1.caption(f"Llama 3 knows you have {len(current_inventory)} ingredients. Just ask naturally.")
    if col2.button("🗑️", help="Clear chat", disabled=not st.session_state.chat_history):
        st.session_state.chat_history = []
        st.rerun()

    # ── DIETARY RESTRICTIONS: multiselect above chat ──────────────────────────
    st.multiselect(
        "Dietary preferences",
        options=["Vegan", "Vegetarian", "Gluten-Free", "Dairy-Free", "Nut-Free", "Halal", "Kosher"],
        key="dietary_restrictions",
        placeholder="No dietary restrictions — select any that apply",
        label_visibility="collapsed",
    )
    # ─────────────────────────────────────────────────────────────────────────

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ── SHOPPING LIST: button appears after any recipe response ───────────────
    _last_asst = next(
        (m for m in reversed(st.session_state.chat_history) if m["role"] == "assistant"),
        None,
    )
    if _last_asst and "### Ingredients" in _last_asst["content"]:
        _recipe_ings = extract_recipe_ingredients(_last_asst["content"])
        _missing = get_missing_ingredients(_recipe_ings, current_inventory)
        if _missing:
            _b1, _b2 = st.columns([3, 1])
            _b1.markdown("**Missing:** " + ", ".join(f"`{i}`" for i in _missing))
            if _b2.button("🛒 Add to shopping list", type="primary"):
                _existing_sl = load_shopping_list()
                _merged_sl = sorted(set(_existing_sl) | set(_missing))
                save_shopping_list(_merged_sl)
                st.success(f"✅ Added {len(_missing)} item(s) to your shopping list.")
                st.rerun()
        else:
            st.caption("✅ You have everything for this recipe.")
    # ─────────────────────────────────────────────────────────────────────────

    user_input = st.chat_input("Ask your AI chef anything...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            assistant_response = st.write_stream(
                stream_chef_response(
                    user_message=user_input,
                    inventory=current_inventory,
                    history=st.session_state.chat_history[:-1],
                    dietary_restrictions=st.session_state.dietary_restrictions or None,
                )
            )

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        st.rerun()
