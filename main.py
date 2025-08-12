import logging
import io
import requests
import pdfplumber
import tiktoken
from litellm import completion
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, constr
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cache = TTLCache(maxsize=100, ttl=3600)

# Load system prompt
with open("prompt_system.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Tokenizer setup
enc = tiktoken.encoding_for_model("gpt-4o")
encode, decode = enc.encode, enc.decode

# Config class
class Config:
    MAX_TOKEN_INPUT = int(os.getenv("MAX_TOKEN_INPUT", 31000))
    MAX_TOKEN_OUTPUT = int(os.getenv("MAX_TOKEN_OUTPUT", 5000))
    MODEL_NAME = os.getenv("MODEL_NAME", "openai/cpatonn/Qwen3-4B-Instruct-2507-AWQ")
    API_BASE = os.getenv("API_BASE", "http://1.53.58.232:8521/v1")
    API_KEY = os.getenv("API_KEY", "EMPTY")
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))
    TOP_P = float(os.getenv("TOP_P", 0.8))
    TOP_K = int(os.getenv("TOP_K", 20))
    STREAM = os.getenv("STREAM", "true").lower() == "true"
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")

# PDF processing
def extract_text_from_pdf(url):
    resp = requests.get(url)
    resp.raise_for_status()
    with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

# Truncate to max tokens
def truncate_text(text, max_tokens=Config.MAX_TOKEN_INPUT):
    tokens = encode(text)
    if len(tokens) <= max_tokens:
        return text
    return decode(tokens[:max_tokens])

# Inference
def run_inference(content):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content}
    ]
    response = completion(
        model=Config.MODEL_NAME,
        api_base=Config.API_BASE,
        api_key=Config.API_KEY,
        messages=messages,
        max_tokens=Config.MAX_TOKEN_OUTPUT,
        temperature=Config.TEMPERATURE,
        top_p=Config.TOP_P,
        top_k=Config.TOP_K,
        stream=Config.STREAM
    )
    for chunk in response:
        if delta := chunk.choices[0].delta.content:
            yield delta

# FastAPI app
app = FastAPI()

class PDFRequest(BaseModel):
    pdf_url: constr(max_length=2048)

@app.post("/summarize_pdf")
async def summarize_pdf(request: PDFRequest):
    url = request.pdf_url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="PDF URL required")

    if url in cache:
        return JSONResponse(content={"summary": cache[url]})

    try:
        full_text = extract_text_from_pdf(url)
        if not full_text:
            raise HTTPException(status_code=400, detail="No text found in PDF")

        input_text = truncate_text(full_text)
        summary = "".join(run_inference(input_text))

        cache[url] = summary
        return JSONResponse(content={"summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream_summary")
async def stream_summary(request: PDFRequest):
    url = request.pdf_url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="PDF URL required")

    try:
        full_text = extract_text_from_pdf(url)
        if not full_text:
            raise HTTPException(status_code=400, detail="No text found in PDF")

        input_text = truncate_text(full_text)
        return StreamingResponse(run_inference(input_text), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)