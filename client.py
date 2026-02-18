import base64

import streamlit as st
import requests
from PIL import Image
import io
import json
from pathlib import Path

from utils.ollama_client import generate_with_image


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
    st.image(image, caption="Fridge scan", use_container_width=True)

if st.button("🔍 Scan Ingredients", type="primary", disabled=image_bytes is None):
    assert image_bytes is not None
    with st.spinner("Scanning ingredients..."):
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "List every food item you see in this fridge image. "
            "Return as comma-separated list only. No extra text."
        )
        new_items: list = []
        try:
            raw = generate_with_image(prompt, image_b64)
            new_items = [item.strip() for item in raw.split(",") if item.strip()]
        except Exception as e:
            st.error(f"Scan failed: {e}")
            st.stop()

    existing = load_inventory()
    merged = merge_ingredients(existing, new_items)
    save_inventory(merged)
    st.success(f"✅ {len(new_items)} ingredients detected. Inventory now has {len(merged)} items.")
    st.rerun()

st.divider()

# ── SECTION 3: CHAT ───────────────────────────────────────────────────────────
st.subheader("💬 What Can I Cook?")

current_inventory = load_inventory()

if not current_inventory:
    st.warning("Scan some ingredients first — then ask me what to cook.")
else:
    st.caption(f"Llama 3 knows you have {len(current_inventory)} ingredients. Just ask naturally.")

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
                assistant_response = "TODO: wire to ollama_client.generate_text()"
                st.markdown(assistant_response)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_response}
        )

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
