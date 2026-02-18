import requests, base64

with open("test.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

resp = requests.post("http://100.75.28.113:11434/api/generate", json={
    "model": "llava:13b",
    "prompt": "List all food items you see. Be specific.",
    "images": [img_b64],
    "stream": False
})
print(resp.json()["response"])