# Run YOLO World service on GB10

**Test on this branch first; merge to main only after GB10 tests pass.**

On the **Dell GB10** machine (where Mac connects via Tailscale):

## 1. Clone / pull and checkout branch

```bash
# If repo already exists
cd /path/to/fridge-to-fork
git fetch origin
git checkout model/yolo
git pull origin model/yolo

# First-time clone
git clone https://github.com/Jeremy891102/fridge-to-fork.git
cd fridge-to-fork
git checkout model/yolo
```

## 2. Python env (3.9+)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux; on Windows: .venv\Scripts\activate
```

## 3. Install dependencies (GB10 only)

```bash
pip install ultralytics fastapi uvicorn pillow numpy pydantic
```

Optional: add to `requirements.txt` and use `pip install -r requirements.txt` if you add a `requirements-gb10.txt`.

## 4. Run YOLO service

```bash
# Default port 8001
uvicorn yolo_service:app --host 0.0.0.0 --port 8001
```

Or:

```bash
python yolo_service.py
```

- Ensure `data/fridge_ontology.json` exists (in repo).
- First request will download the model (`yolov8s-worldv2.pt`) if needed.

## 5. Check

- Health: `curl http://localhost:8001/health`
- From Mac (replace with GB10 Tailscale IP): set in `.env` on Mac:
  - `YOLO_SERVICE_URL=http://100.75.28.113:8001`

## Optional env (on GB10)

- `YOLO_PORT=8001` — port (default 8001)
- `YOLO_MODEL=yolov8s-worldv2.pt` — model id (default)

---

After testing passes, merge `model/yolo` into `main`.
