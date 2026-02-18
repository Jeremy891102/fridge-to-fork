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

### 5. Run the Application

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
