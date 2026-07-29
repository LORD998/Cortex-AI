# Cortex AI

A local, privacy-first AI assistant for Windows. Powered by an Ollama brain, offline voice synthesis, computer vision, local memory, and a real tool-use agentic loop to interact with files, applications, and services.

## 🚀 Overview

Cortex AI is built to be a truly local personal assistant. It combines cutting-edge local LLMs (like `qwen3:8b`) with a multi-step reasoning agent architecture. It can think, choose contextual tools, execute them, and verify the results—all while keeping your data strictly on your machine.

### Key Features
- **Local Conversational AI**: Powered by `qwen3:8b` via Ollama for fast, uncensored, and private interactions.
- **Multi-Step Agent Loop**: The assistant reasons through tasks, uses tools, checks outcomes, and iterates until the goal is achieved.
- **Contextual Tool Routing**: Dynamically supplies only the relevant tools to the LLM out of a pool of 55+ available actions, saving context window and improving accuracy.
- **Offline Speech-to-Text & Text-to-Speech**: Uses `faster-whisper` for incredibly fast and accurate transcription, and Kokoro/Piper for high-quality, natural-sounding offline neural voices.
- **Computer Vision**: Leverages `qwen3-vl:8b` to see and analyze your screen.
- **Long-term Memory**: Persists conversational context and user preferences locally in a JSON store.
- **Real-Time Call Translation**: Auto-detects languages, translates locally, and outputs to a virtual audio cable for seamless use in Discord or Zoom.
- **Deep System Integration**: Features tools for file management, window control, keyboard/mouse automation, and optional internet integrations (e.g., Gmail, web search).

## 🧠 Architecture: How it Works

Cortex AI is structured around a modular agentic framework:

1. **Input Processing**: The `voice_manager` handles continuous listening. When a user speaks, the audio is processed locally using `faster-whisper`.
2. **Context & Routing (`tool_router.py`)**: Before hitting the main LLM, a fast lightweight intent classifier determines the context of the user's request. It selects only the necessary tools, passing them to the main orchestrator.
3. **Reasoning Engine (`orchestrator.py`)**: 
   - **Fast Mode**: For simple queries, it directly answers.
   - **Deep Reasoning Mode**: For complex tasks, it enters a loop. It analyzes the problem, formulates a plan, executes a tool (like reading a file or searching the web), evaluates the tool's output, and decides if it needs to take another step.
4. **Execution & Safeguards**: Any action that modifies the system (deleting files, sending emails, running terminal commands) is intercepted and requires explicit user confirmation.
5. **Output Generation (`local_speech.py`)**: The generated text is passed to the local TTS engine (Kokoro or Piper) for instant, natural playback.

## 🔒 Privacy & Security First

- **100% Local Inference**: Once models are downloaded, core functions (brain, voice recognition, translation, TTS) require **no internet connection**. No audio or text is sent to the cloud.
- **Explicit Consents**: The system will explicitly ask for permission before performing destructive or external actions (e.g., sending emails, deleting files, installing software, closing applications).

## 🛠️ Installation & Setup

### Prerequisites
- Windows 10 or 11
- Python 3.11+
- [Ollama](https://ollama.ai/) installed locally
- A microphone
- (Optional but recommended) A dedicated GPU for faster inference

### Setup Guide

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/cortex-ai.git
   cd cortex-ai
   ```

2. **Install dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Download Local Voice Models**
   ```bash
   python scripts/setup_local_voice.py
   ```

4. **Pull Ollama Models**
   ```bash
   ollama pull qwen3:8b
   ollama pull qwen3-vl:8b
   ```

## 💻 Usage

To start Cortex AI:
```bash
python cortex_overlay.py
```
*(Alternatively, use `start_cortex_hidden.vbs` to run it silently in the background.)*

**Hotkeys & Commands:**
- Hold `ALT` to speak, release to send the command.
- Press `0` to toggle the real-time call translator.
- Say *"English teacher mode"* to start an interactive learning session.

## ⚙️ Configuration

Copy `.env.example` to `.env` to customize settings:

```dotenv
CORTEX_MODEL=qwen3:8b
CORTEX_CONTEXT_SIZE=8192
CORTEX_REASONING=auto
CORTEX_WHISPER_MODEL=small
CORTEX_TTS_ENGINE=kokoro
CORTEX_TTS_SPEED=1.0
```

- `CORTEX_REASONING=auto`: Automatically switches to deep reasoning for multi-step tasks. Can be set to `on` or `off`.
- `CORTEX_WHISPER_MODEL`: Change to `medium` for better multi-language recognition (requires more VRAM).

## 🧪 Testing

The project includes an extensive test suite. Manual tests (involving hardware like the microphone) are separated from automated logic tests.

```bash
# Run logic tests
python -m unittest discover -s tests -v
```

## 📁 Project Structure
```text
core/
  ├── config.py          # Central configuration management
  ├── nlp_engine.py      # Ollama client & LLM interfacing
  ├── orchestrator.py    # Main agent loop and tool execution
  └── tool_router.py     # Contextual tool selection
modules/
  ├── local_speech.py    # Whisper, Piper, and Kokoro integrations
  ├── voice_manager.py   # Microphone and audio processing
  ├── email_manager.py   # Gmail integration with draft-first safety
  └── ...
tests/                 # Automated test suite
scripts/               # Setup and manual hardware testing scripts
```
