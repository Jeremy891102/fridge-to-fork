# Fridge-to-Fork workflow

## End-to-end flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Mac (Streamlit — client.py)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ 1. User uploads/camera photo
         │ 2. Clicks "Scan Ingredients"
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  core.vision.extract_ingredients(image_bytes)                                 │
│  → utils.yolo_client.detect_ingredients(image_bytes)                         │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ 3. HTTP POST image (base64) to GB10
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GB10 — YOLO service (yolo_service.py :8001)                                 │
│  POST /detect → YOLO-World inference → {"labels": ["egg", "milk", ...]}     │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ 4. Return list of detected ingredients
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Mac — merge into inventory.json, show in "My Fridge Inventory"             │
└─────────────────────────────────────────────────────────────────────────────┘

         │ 5. User types in chat: "What can I cook?"
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  core.recipe.chat_with_chef(message, inventory, history)                     │
│  → utils.ollama_client.generate_text(prompt)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ 6. HTTP POST prompt to GB10 Ollama
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  GB10 — Ollama (port 11434)                                                  │
│  LLaMA 3.1:8b → recipe / chat response                                       │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ 7. Return text
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Mac — display assistant message in chat                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Summary

| Step | Where | What |
|------|--------|------|
| Scan photo | Mac | User picks upload or camera → gets `image_bytes` |
| Detect ingredients | Mac → GB10 | `extract_ingredients(image_bytes)` → `yolo_client` POST to YOLO service → YOLO-World → labels |
| Save inventory | Mac | Merge labels into `inventory.json`, show in UI |
| Chat | Mac | User message + inventory + history → `chat_with_chef()` |
| Generate reply | Mac → GB10 | `ollama_client.generate_text(prompt)` → Ollama LLaMA → response |
| Show reply | Mac | Append to chat history |

## Services on GB10

- **Ollama** (port 11434): LLaMA 3.1:8b for recipe/chat. Used by `utils.ollama_client`.
- **YOLO service** (port 8001): YOLO-World for ingredient detection. Used by `utils.yolo_client`.

## Note

`client.py` must use **core.vision.extract_ingredients(image_bytes)** for the scan step so that detection goes through YOLO. If it calls **generate_with_image** instead, scan still uses LLaVA on Ollama.
