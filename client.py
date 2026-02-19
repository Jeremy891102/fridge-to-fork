import hashlib
import io
import json
from pathlib import Path

import streamlit as st
from PIL import Image

from core.recipe import chat_with_chef, ingredients_to_recipe
from core.vision import extract_ingredients


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

# ── SECTION 2: SCAN ───────────────────────────────────────────────────────────
st.subheader("📷 Upload fridge or ingredients photo")
st.caption("Detection runs automatically after upload or capture — no button to press.")

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
    camera_file = st.camera_input("Point at your fridge or ingredients")
    if camera_file is not None:
        image_bytes = camera_file.read()
        image = Image.open(io.BytesIO(image_bytes))

if image is not None:
    st.image(image, caption="Uploaded", use_container_width=True)

if image_bytes is not None:
    img_hash = hashlib.md5(image_bytes).hexdigest()
    if img_hash != st.session_state.last_scanned_hash:
        with st.spinner("Detecting ingredients..."):
            try:
                new_items = extract_ingredients(image_bytes)
                existing = st.session_state.pending_scan or []
                seen = {i.lower() for i in existing}
                for item in new_items:
                    if item.lower() not in seen:
                        existing.append(item)
                        seen.add(item.lower())
                st.session_state.pending_scan = existing
                st.session_state.last_scanned_hash = img_hash
                if not new_items:
                    st.warning("No ingredients detected. Check that YOLO_SERVICE_URL in .env points to GB10 (e.g. http://100.75.28.113:8001) and the service is running, or try another photo.")
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
        st.success(f"✅ Added {len(confirmed)} items. Inventory now has {len(merged)} items.")
        st.rerun()

st.divider()

# ── SECTION 3: CHAT ───────────────────────────────────────────────────────────
st.subheader("💬 What Can I Cook?")

current_inventory = load_inventory()


def build_chat_prompt(user_message: str, inventory: list[str], history: list[dict]) -> str:
    inv = "\n".join(f"- {x}" for x in inventory)

    recent = history[-6:]
    history_txt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)

    return f"""You are an AI chef assistant.

Rules:
- Prioritize using the inventory items as primary ingredients.
- You may add at most 3 pantry staples from: salt, pepper, oil, water, sugar, soy sauce, butter, garlic, onion.
- If the user asks "what can I cook", propose 2 options max, each with short steps.
- If the user asks for one recipe, return one detailed recipe with steps.
- No unnecessary commentary.

Current inventory:
{inv}

Conversation so far:
{history_txt}

USER: {user_message}
ASSISTANT:
"""


if not current_inventory:
    st.warning("Scan some ingredients first — then ask me what to cook.")
else:
    col1, col2 = st.columns([8, 1])
    col1.caption(f"Llama 3 knows you have {len(current_inventory)} ingredients. Just ask naturally.")
    if col2.button("🗑️", help="Clear chat", disabled=not st.session_state.chat_history):
        st.session_state.chat_history = []
        st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask your AI chef anything...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Chef is thinking..."):
                
                assistant_response = chat_with_chef(
                    user_message=user_input,
                    inventory=current_inventory,
                    history=st.session_state.chat_history[:-1],  # exclude current user message
                )
                st.markdown(assistant_response)

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        st.rerun()
