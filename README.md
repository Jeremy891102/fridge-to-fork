# 🍳 Fridge-to-Fork

An intelligent recipe generation app that automatically identifies ingredients from photos of your fridge or ingredients and generates personalized recipes.

## 📖 About

Fridge-to-Fork is an AI-powered recipe recommendation system based on computer vision and natural language processing. Simply take a photo of your fridge or ingredients, and the app will automatically identify the ingredients and generate suitable recipe suggestions based on what you have.

### ✨ Features

- 📸 **Image Recognition**: Uses LLaVA vision model to identify ingredients in photos
- 🥗 **Ingredient Extraction**: Automatically extracts ingredient lists from images
- 👨‍🍳 **Recipe Generation**: Generates detailed recipe steps based on identified ingredients
- 🎨 **Clean Interface**: Modern web interface built with Streamlit

## 🛠️ Tech Stack

- **Frontend Framework**: Streamlit
- **AI Model**: Ollama (LLaVA 13B)
- **Image Processing**: Pillow
- **HTTP Client**: Requests
- **Configuration Management**: python-dotenv

## 📋 Prerequisites

- Python 3.8+
- Running Ollama server (with LLaVA 13B or similar vision model installed)
- Network connection (for accessing Ollama API)

### Installing Ollama and Model

If you haven't installed Ollama yet, install it first:

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull the LLaVA 13B model
ollama pull llava:13b
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Jeremy891102/fridge-to-fork.git
cd fridge-to-fork
```

### 2. Create Virtual Environment (Recommended)

```bash
# Using venv
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the environment variable example file
cp .env.example .env

# Edit the .env file and modify the following variables according to your Ollama server configuration:
# GB10_IP=100.75.28.113      # Ollama server IP address
# OLLAMA_PORT=11434         # Ollama server port
# MODEL=llava:13b           # Model name to use
```

### 5. Test Ollama Connection (隊友 pull 下來後必做)

確認能打到 Ollama 再跑 app：

```bash
# 方式一：跑內建測試（健康檢查 + 一句話生成）
python utils/ollama_client.py
```

預期輸出類似：
```
Health check: True
Text test:  Hello
```

若連線失敗會報錯或 `Health check: False`。請檢查：
- 是否有建立 `.env`（`cp .env.example .env`）
- `.env` 裡的 `GB10_IP`、`OLLAMA_PORT` 是否與實際 Ollama 伺服器一致
- 本機或網路能否連到該 IP（例如 `curl http://<GB10_IP>:<OLLAMA_PORT>`）

```bash
# 方式二：較詳細的測試腳本（含目前使用的 BASE_URL）
python scripts/test_ollama.py
```

### 6. Run the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser (usually at `http://localhost:8501`).

## 📁 Project Structure

```
fridge-to-fork/
├── app.py                  # Main Streamlit application entry point
├── core/                   # Core business logic
│   ├── __init__.py
│   ├── vision.py          # Image recognition module: image → ingredient list
│   └── recipe.py           # Recipe generation module: ingredient list → recipe
├── utils/                  # Utility modules
│   ├── __init__.py
│   └── ollama_client.py    # Ollama API client: all HTTP calls
├── .env.example            # Environment variable example file
├── .env                    # Actual environment variable file (create this)
├── .gitignore             # Git ignore file configuration
├── requirements.txt        # Python dependencies list
└── README.md              # Project documentation
```

### Module Descriptions

- **`app.py`**: Main Streamlit application that handles user interface and interaction logic
- **`core/vision.py`**: Calls `ollama_client` vision API to extract ingredients from images
- **`core/recipe.py`**: Calls `ollama_client` text generation API to generate recipes from ingredients
- **`utils/ollama_client.py`**: Encapsulates all communication with Ollama API, including image and text generation

## 🎯 Usage

1. **Start the app**: Run `streamlit run app.py`
2. **Upload an image**: Click the upload button in the web interface and select a photo containing ingredients (supports JPG, JPEG, PNG formats)
3. **View ingredients**: The app will automatically identify and display the detected ingredient list
4. **Generate recipe**: Click the "Generate recipe" button, and the system will generate a detailed recipe based on the identified ingredients

## ⚙️ Configuration

### Environment Variables

Configure the following variables in the `.env` file:

- **`GB10_IP`**: Ollama server IP address (default: `100.75.28.113`)
- **`OLLAMA_PORT`**: Ollama server port (default: `11434`)
- **`MODEL`**: Model name to use (default: `llava:13b`)

### Local Ollama Server

If Ollama is running locally, you can set:

```env
GB10_IP=localhost
OLLAMA_PORT=11434
MODEL=llava:13b
```

## 🔧 Troubleshooting

### Issue: Cannot connect to Ollama server

- Check if the Ollama server is running
- Verify that the IP and port configuration in `.env` file is correct
- Check firewall settings to ensure Ollama server is accessible

### Issue: Model not found

- Confirm that the specified model is installed: `ollama pull llava:13b`
- Check if the `MODEL` variable in `.env` file is correct

### Issue: Image recognition fails

- Ensure uploaded images are clear and ingredients are visible
- Try photos from different angles or lighting conditions
- Check if the image format is supported (JPG, JPEG, PNG)

### Issue: Dependency installation fails

- Ensure you're using Python 3.8 or higher
- Try upgrading pip: `pip install --upgrade pip`
- Use a virtual environment to avoid dependency conflicts

## 🧪 Development

### Code Style

This project follows the **Google Python Style Guide**. See [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed guidelines.

Key points:
- Maximum line length: 80 characters
- Use type hints for all functions
- Google-style docstrings required
- Follow import order: stdlib → third-party → local
- Use TODO comments to mark incomplete features

### Running Tests

The project currently includes basic functionality implementation. You can test it by:

```bash
# Ensure Ollama server is running
# Start the app and upload a test image
streamlit run app.py
```

### Code Quality Tools

```bash
# Format code (requires black)
black .

# Sort imports (requires isort)
isort .

# Lint code (requires pylint)
pylint app.py core/ utils/

# Type check (requires mypy)
mypy app.py core/ utils/
```

### Suggested Extensions

See TODO comments throughout the codebase for planned features:

- Add recipe saving functionality
- Support multiple image uploads
- Add ingredient editing functionality
- Implement recipe rating and favorites
- Add multi-language support
- Add error handling and retry logic
- Implement response caching
- Add input validation
- Support streaming responses

## 📝 License

This is a Hackathon project. Please add license information according to your actual needs.

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📧 Contact

For questions or suggestions, please contact via GitHub Issues.

## 分工與完整 Pipeline

---

## 三人分工

| 人 | 負責檔案 | 狀態 |
|----|---------|------|
| **你 (Jeremy)** | `utils/ollama_client.py` | 🔨 進行中 |
| **隊友 A** | `core/vision.py` | ⏳ 等你完成 |
| **隊友 B** | `core/recipe.py` | ⏳ 等你完成 |
| **整合（三人一起）** | `app.py` | ⏳ 最後做 |

---

## 完整 Pipeline

```
用戶上傳冰箱照片 (app.py)
         ↓
  轉成 base64 (app.py)
         ↓
extract_ingredients(image_bytes)  ← 隊友A寫
         ↓
generate_with_image(prompt, base64) ← 你寫
         ↓
POST /api/generate to GB10 Ollama
         ↓
回傳 "eggs, tomatoes, cheese, milk"
         ↓
parse 成 list ["eggs","tomatoes"...]  ← 隊友A寫
         ↓
顯示食材清單 (app.py)
         ↓
用戶點 Generate Recipe
         ↓
generate_recipe(ingredients)  ← 隊友B寫
         ↓
generate_text(prompt)  ← 你寫
         ↓
POST /api/generate to GB10 Ollama
         ↓
回傳完整食譜文字
         ↓
顯示食譜 (app.py)
```

---

## 每個檔案的細節

### 你 → `utils/ollama_client.py`
```
輸入：prompt (str), image_base64 (str, 選填)
輸出：Ollama 回傳的文字 (str)
對外暴露：
  - health_check()
  - generate_with_image()
  - generate_text()
```

### 隊友 A → `core/vision.py`
```
輸入：image_bytes (用戶上傳的原始圖片)
輸出：ingredients list ["egg", "milk", ...]
步驟：
  1. image_bytes → base64 string
  2. 呼叫 generate_with_image()
  3. 把回傳字串 split by "," → list
  4. 清理空白 strip()
Prompt 用這個：
  "List every food item you see in this fridge image. 
   Return as comma-separated list only. No extra text."
```

### 隊友 B → `core/recipe.py`
```
輸入：ingredients list ["egg", "milk", ...]
輸出：食譜文字 (str)
步驟：
  1. list → join 成字串 "egg, milk, ..."
  2. 呼叫 generate_text()
  3. 直接回傳食譜文字
Prompt 用這個：
  "You are a gourmet chef. Create a detailed recipe 
   using ONLY these ingredients: {ingredients}. 
   Include: dish name, prep time, step-by-step instructions."
```

### 整合 → `app.py`（最後一起做）
```
步驟：
  1. health_check() → 確認 GB10 連線
  2. st.file_uploader → 拿到 image_bytes
  3. 呼叫 extract_ingredients(image_bytes)
  4. 顯示食材
  5. 呼叫 generate_recipe(ingredients)
  6. 顯示食譜
```

---

## 開發順序

```
Step 1: 你完成 ollama_client.py 並測試通過
           ↓
Step 2: push 到 main
           ↓
Step 3: 隊友 A & B 同時開始（各自 branch）
           ↓
Step 4: 各自測試完 push PR
           ↓
Step 5: 三人一起整合 app.py
           ↓
Step 6: Demo！
```

---

## 現在行動

- **你** → 繼續完成 `ollama_client.py` → 測試 → push main
- **隊友 A** → 等你 push 完，clone 最新 main，開 `feat/vision` branch
- **隊友 B** → 等你 push 完，clone 最新 main，開 `feat/recipe` branch
