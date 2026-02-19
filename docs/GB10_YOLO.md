# Run YOLO World service on GB10

**先在此 branch 上測試，GB10 測完沒問題再 merge 到 main。**

On the **Dell GB10** machine (where Mac connects via Tailscale):

## 1. Clone / pull 並切到 branch 測試

```bash
# 若已有 repo
cd /path/to/fridge-to-fork
git fetch origin
git checkout model/yolo
git pull origin model/yolo

# 若第一次 clone
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
  - `YOLO_SERVICE_URL=http://<GB10_TAILSCALE_IP>:8001`

## Optional env (on GB10)

- `YOLO_PORT=8001` — port (default 8001)
- `YOLO_MODEL=yolov8s-worldv2.pt` — model id (default)

---

**測試無誤後** 再在 repo 裡把 `model/yolo` merge 到 `main`。
