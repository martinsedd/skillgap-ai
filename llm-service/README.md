# SkillGap LLM Service

Local LLM inference service using llama.cpp for skill extraction and gap analysis.

## Setup

### 1. Download Model

Download Mistral-7B-Instruct-v0.3 Q5_K_M quantization:

```bash
mkdir -p models

wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q5_K_M.gguf \
-O models/mistral-7b-instruct-v0.3.Q5_K_M.gguf
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your model path and settings
```

### 3. Run Service

```bash
uv run python main.py
```

The service will be available at http://localhost:8001

## API Endpoints

Health Check

```bash
curl http://localhost:8001/health
```

Generate Text

```bash
curl -X POST http://localhost:8001/generate \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Extract technical skills from this resume: ...",
        "max_tokens": 512,
        "temperature": 0.3
    }'
```

## Performance Notes

- GPU Layers: More layers = faster but uses more VRAM
- Context Size: Larger = more context but slower
- Temperature: Lower (0.1-0.3) for structured output like JSON
- Expected Latency: 2-5 seconds per request on modern hardware

Once you've created these files and have the model downloaded, test it:

```bash
cd llm-service
cp .env.example .env

uv run python main.py

curl http://localhost:8001/healht
```
