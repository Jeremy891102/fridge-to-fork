#!/usr/bin/env python3
"""Quick test: can this machine reach the Ollama server?

Run after pull to verify .env and network:
  python scripts/test_ollama.py

Or from project root:
  python -m scripts.test_ollama
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from utils.ollama_client import BASE_URL, generate_text, health_check


def main() -> None:
    print("Fridge-to-Fork — Ollama connection test")
    print("=" * 50)
    print(f"Target: {BASE_URL}")
    print(f"  GB10_IP   = {os.getenv('GB10_IP', '(not set, default localhost)')}")
    print(f"  OLLAMA_PORT = {os.getenv('OLLAMA_PORT', '(not set, default 11434)')}")
    print()

    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")):
        print("Warning: No .env file. Create one with: cp .env.example .env")
        print()

    print("1. Health check (GET request)...")
    ok = health_check()
    if not ok:
        print("   FAILED — Cannot reach Ollama server.")
        print("   Check: server running? .env correct? firewall?")
        sys.exit(1)
    print("   OK — Server is reachable.")
    print()

    print("2. Text generation (POST /api/generate)...")
    try:
        out = generate_text("say hello in one word")
        print(f"   OK — Model replied: {out.strip()}")
    except Exception as e:
        print(f"   FAILED — {e}")
        sys.exit(1)

    print()
    print("All checks passed. You can run the app: streamlit run app.py")


if __name__ == "__main__":
    main()
