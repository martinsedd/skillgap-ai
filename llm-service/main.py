import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from llama_cpp import Llama
from pydantic import BaseModel, Field

load_dotenv()

# Load environment varibles
MODEL_PATH = os.getenv("MODEL_PATH", "/models/mistral-7b-instruct-v0.3.Q5_K_M.gguf")
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "35"))
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "4096"))
THREADS = int(os.getenv("THREADS", "8"))

llm: Llama | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm
    print(f"Loading model from {MODEL_PATH}...")
    print(f"GPU layers: {GPU_LAYERS}, Context size: {CONTEXT_SIZE}")

    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=CONTEXT_SIZE,
        n_threads=THREADS,
        verbose=False,
    )
    print("Model loaded successfully")

    yield

    print("Shutting down LLM service...")
    llm = None


app = FastAPI(title="SkillGap LLM Service", version="1.0.0", lifespan=lifespan)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The prompt to send to the LLM")
    max_tokens: int = Field(
        512, ge=1, le=2048, description="Maximum tokens to generate"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stop: list[str] | None = Field(None, description="Stop sequences")


class GenerateResponse(BaseModel):
    text: str
    tokens_generated: int
    finish_reason: str


@app.get("/health")
async def health():
    if llm is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_lodade": True}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if llm is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = llm(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop or [],
            echo=False,
        )

        if isinstance(result, dict):
            return GenerateResponse(
                text=result["choices"][0]["text"],
                tokens_generated=result["usage"]["completion_tokens"],  # type: ignore
                finish_reason=result["choices"][0]["finish_reason"],  # type: ignore
            )
        else:
            return GenerateResponse(
                text=str(result),
                tokens_generated=0,
                finish_reason="stop",
            )
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
