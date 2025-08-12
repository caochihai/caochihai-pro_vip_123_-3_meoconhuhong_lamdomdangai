# 🚀 PDF Summarizer API with AI Power 🧠🔥

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai)](https://platform.openai.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/github/license/yourusername/pdf-summarizer?style=for-the-badge)](LICENSE)

## 🌟 Overview

This **PDF Summarizer API** extracts text from a given PDF URL and uses a powerful LLM (Large Language Model) to generate concise, meaningful summaries. Built with **FastAPI**, it supports both **synchronous** and **streaming** responses for real-time interaction.

Perfect for quickly understanding large documents like research papers, contracts, or reports.

---

## 🧰 Features

- 🔍 Extracts text from remote PDF URLs
- 📏 Automatically truncates input to fit model token limits
- 💬 Summarizes content using advanced LLMs (Qwen, GPT, etc.)
- ⚡ Caching for faster repeated queries
- 🔄 Streaming support for real-time response
- 🛡️ Built with FastAPI – fast, async-ready, and auto-documented

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/pdf-summarizer.git
cd pdf-summarizer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the root directory:

```env
MODEL_NAME=openai/cpatonn/Qwen3-4B-Instruct-2507-AWQ
API_BASE=http://1.53.58.232:8521/v1
API_KEY=EMPTY
MAX_TOKEN_INPUT=31000
MAX_TOKEN_OUTPUT=5000
TEMPERATURE=0.2
TOP_P=0.8
TOP_K=20
STREAM=true
PORT=5000
HOST=0.0.0.0
```

### 4. Add your system prompt

Make sure you have a `prompt_system.md` file in the root directory to guide the summarization behavior.

### 5. Run the app

```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

Or using the script:

```bash
python main.py
```

---

## 🧪 API Endpoints

### 🔹 POST `/summarize_pdf`

Summarize a PDF from a URL.

**Request:**

```json
{
  "pdf_url": "https://example.com/sample.pdf"
}
```

**Response:**

```json
{
  "summary": "This is a concise summary of the PDF..."
}
```

---

### 🔹 POST `/stream_summary`

Stream a summary in real-time using Server-Sent Events (SSE).

**Request:**

```json
{
  "pdf_url": "https://example.com/sample.pdf"
}
```

**Response:**

> Streams tokens in real-time via `text/event-stream`.

---

## 🧠 Supported Models

You can configure any LiteLLM-compatible model:

- Qwen3 4B (default)
- GPT-4, GPT-3.5-turbo
- Llama 3, Mistral, and more

---

## 🛠️ Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- pdfplumber
- requests
- tiktoken
- litellm
- cachetools
- python-dotenv

Install via:

```bash
pip install -r requirements.txt
```

---

## 🧾 Example `.env`

```env
MODEL_NAME=openai/cpatonn/Qwen3-4B-Instruct-2507-AWQ
API_BASE=http://1.53.58.232:8521/v1
API_KEY=EMPTY
MAX_TOKEN_INPUT=31000
MAX_TOKEN_OUTPUT=5000
TEMPERATURE=0.2
TOP_P=0.8
TOP_K=20
STREAM=true
PORT=5000
HOST=0.0.0.0
```

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙌 Contributing

Contributions are welcome! Please fork the repo and submit a pull request.

---

## 📬 Contact

Have questions or feedback? Reach out to [your-email@example.com](mailto:your-email@example.com)

---

## 🌈 Made with ❤️ using FastAPI & AI