# Jolly Baron — Local GGUF Translator v0.3

A modular, browser‑based translator powered by [llama‑cpp‑python](https://github.com/abetlen/llama-cpp-python) and [Gradio](https://gradio.app/).  
Works **completely offline** with any GGUF model. Translate between Japanese, English, Russian, French, German and Spanish — add more languages easily.

## ✨ Features

- **Universal model support** — automatically adapts to the model's chat template (Qwen, Mistral, Gemma, Llama 2, etc.)
- **Manual override** — select prompt format from settings (chatml, mistral, gemma, llama2)
- **Line‑by‑line mode** — preserves row count when pasting CSV or plain text
- **Streaming output** — watch the translation appear in real time
- **Stop button** — instantly interrupt a running translation
- **Auto‑save** — every translation is saved to the `Translations/` folder
- **GPU acceleration** — Flash Attention, 8‑bit KV‑cache, automatic GPU layer offloading
- **Splash screen** — personal logo appears on startup (replace `jolly baron.jpg` with your own)
- **Settings persistence** — max tokens, prompt format, system prompt, languages are saved across restarts

### 🧪 Developer notes

- Was made to simplify translation of various text files (like csv) without breaking lines
- Tested with **Ministral-3-14B-abliterated.Q4_K_M.gguf** — works perfectly.
- **Qwen 3.5** works, but gives a lot of problems with "thinking" mode. Feel free to experiment with system prompts to tame it.
- Main development and testing was done on the **Japanese → English** pair.

## 📥 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jolly-Baron/Jolly-Baron-Translator.git
   cd Jolly-Baron-Translator
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate      # Windows
   source venv/bin/activate     # Linux / macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install llama‑cpp‑python with GPU support (NVIDIA)**
   ```bash
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
   ```
   For AMD / Intel GPUs, check the [llama‑cpp‑python docs](https://github.com/abetlen/llama-cpp-python).

5. **Place your GGUF model(s)** in the `Model/` folder (create it if it doesn't exist).

## 🚀 Usage

Double‑click `run.bat` (Windows) or run:
```bash
python app.py
```
A splash screen will appear, then your browser will open the translator interface.

### 🖥️ Interface

- **Translate tab** — select a GGUF model, choose source & target languages, paste text and click «Translate».
- **Settings tab** — adjust temperature, top‑p, max output tokens, prompt format, and **system prompt**.
  The system prompt is automatically updated when languages change, but you can customise it freely.

## 🧩 Customisation

- **Change the splash image** — replace `jolly baron.jpg` with your own logo. The image will be cropped to a square automatically.
- **Add more languages** — edit the `SOURCE_LANGUAGES` and `TARGET_LANGUAGES` lists in `ui.py`.
- **Define per‑model prompts** — open `model_info.json` and add entries like:
  ```json
  {
    "my-model.gguf": {
      "format": "mistral",
      "system_prompt": "You are a translator. Translate exactly as given."
    }
  }
  ```

## 📂 Project structure

```
.
├── app.py               # entry point (splash + Gradio server)
├── config.py            # global settings and logger
├── model_loader.py      # GGUF model loading / unloading
├── prompt_builder.py    # automatic prompt formatting
├── translator.py        # translation logic with streaming and auto‑save
├── ui.py                # Gradio interface
├── model_info.json      # per‑model preset overrides (empty by default)
├── requirements.txt     # Python dependencies
├── run.bat              # quick launcher for Windows
├── jolly baron.jpg      # splash screen logo (replace with your own)
└── .gitignore
```

## 📄 License

This project is provided as open‑source. Feel free to use, modify and share.