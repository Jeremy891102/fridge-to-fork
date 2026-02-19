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
from core.shopping_list import generate_shopping_list_json  

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
if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = None
if "shopping_list_for" not in st.session_state:
    st.session_state.shopping_list_for = ""
if "show_shopping_input" not in st.session_state:
    st.session_state.show_shopping_input = False

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
        col1, col2 = st.columns([8, 1])
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
    

    col1, col2, col3 = st.columns([7, 1, 1])
    col1.caption(f"🧑‍🍳 {len(current_inventory)} ingredients in your fridge. Ask me anything.")

    # Shopping list toggle button — same size as clear chat
    if col2.button("🛒", help="Generate shopping list"):
        st.session_state.show_shopping_input = not st.session_state.show_shopping_input

    # Clear chat button
    if col3.button("🗑️", help="Clear chat", disabled=not st.session_state.chat_history):
        st.session_state.chat_history = []
        st.rerun()

    # Shopping list input — only shown when toggled
    if st.session_state.show_shopping_input:
        with st.container(border=True):
            dish_query = st.text_input(
                "🛒 What dish do you want to shop for?",
                value=st.session_state.shopping_list_for,
                placeholder="e.g., mapo tofu, pasta carbonara",
            )
            col_a, col_b = st.columns([3, 1])
            if col_a.button("✅ Build shopping list", disabled=not dish_query.strip(), use_container_width=True):
                with st.spinner("Building shopping list..."):
                    try:
                        data = generate_shopping_list_json(
                            user_message=dish_query,
                            inventory=current_inventory,
                            history=st.session_state.chat_history,
                        )
                        st.session_state.shopping_list = data
                        st.session_state.shopping_list_for = dish_query
                        st.session_state.show_shopping_input = False
                    except Exception as e:
                        st.error(f"Shopping list failed: {e}")
                        st.session_state.shopping_list = None
            if col_b.button("✕ Cancel", use_container_width=True):
                st.session_state.show_shopping_input = False
                st.rerun()

    if st.session_state.shopping_list:
        data = st.session_state.shopping_list

        with st.expander(f"🧾 Shopping List — {data.get('dish','')}", expanded=True):
            missing = data.get("missing_items", [])
            optional = data.get("optional_items", [])
            already_have = data.get("already_have", [])
            notes = data.get("notes", [])

            st.markdown("**Missing (must buy):**")
            if not missing:
                st.write("None 🎉")
            else:
                df_missing = pd.DataFrame(missing)
                st.dataframe(df_missing, use_container_width=True, hide_index=True)

            st.markdown("**Optional (nice to have):**")
            if optional:
                df_opt = pd.DataFrame(optional)
                st.dataframe(df_opt, use_container_width=True, hide_index=True)
            else:
                st.write("None")

            if already_have:
                st.markdown("**Already have:** " + ", ".join(already_have))

            if notes:
                st.markdown("**Notes:**")
                for n in notes:
                    st.write(f"- {n}")

            # --- Exports ---
            # CSV: only missing+optional (export-friendly)
            export_rows = []
            for row in missing:
                export_rows.append({**row, "list_type": "missing"})
            for row in optional:
                export_rows.append({**row, "list_type": "optional"})

            df_export = pd.DataFrame(export_rows)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")

            # TXT: simple checklist
            txt_lines = []
            txt_lines.append(f"Shopping List for: {data.get('dish','')}")
            txt_lines.append("")
            txt_lines.append("MISSING:")
            for r in missing:
                q = r.get("quantity")
                u = r.get("unit")
                qty = f"{q} {u}".strip() if q is not None else (u or "").strip()
                qty = f" ({qty})" if qty else ""
                txt_lines.append(f"- {r.get('name','')}{qty}")
            txt_lines.append("")
            txt_lines.append("OPTIONAL:")
            for r in optional:
                q = r.get("quantity")
                u = r.get("unit")
                qty = f"{q} {u}".strip() if q is not None else (u or "").strip()
                qty = f" ({qty})" if qty else ""
                txt_lines.append(f"- {r.get('name','')}{qty}")
            txt_lines.append("")
            if already_have:
                txt_lines.append("ALREADY HAVE: " + ", ".join(already_have))
            txt = "\n".join(txt_lines)

            c1, c2, c3 = st.columns([1, 1, 1])
            c1.download_button(
                "⬇️ Download CSV",
                data=csv_bytes,
                file_name="shopping_list.csv",
                mime="text/csv",
                use_container_width=True,
            )
            c2.download_button(
                "⬇️ Download TXT",
                data=txt.encode("utf-8"),
                file_name="shopping_list.txt",
                mime="text/plain",
                use_container_width=True,
            )
            if c3.button("🧹 Clear list", use_container_width=True):
                st.session_state.shopping_list = None
                st.session_state.shopping_list_for = ""
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
            assistant_response = st.write_stream(
                stream_chef_response(
                    user_message=user_input,
                    inventory=current_inventory,
                    history=st.session_state.chat_history[:-1],
                )
            )

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        st.rerun()
