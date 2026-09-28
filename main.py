from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import os
import uuid
import tempfile

import torch
import torchaudio as ta
from wazobiavoice_tts.mtl_tts import WazobiaVoiceMultilingualTTS

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = None  # loaded once at startup, reused across requests

# WazobiaVoice's 13 built-in personas are selected by feeding a short reference
# clip of that speaker into audio_prompt_path (see model card "How to Use").
# The model repo itself doesn't ship these as named files anywhere obvious in
# the docs, so you need to either:
#   1. Pull the reference clips the repo's own demo apps (multilingual_app.py
#      etc.) use internally for each persona, and drop them in a "voices/"
#      folder here named exactly as below, OR
#   2. Record/collect your own 5-10s clip per character and point these at
#      those instead.
# Until real files exist at these paths, only "language_id" (no persona
# voice) will work — that will use the model's default conditioning voice
# rather than a picked one of the 13, which won't be a Pidgin-specific speaker.
VOICE_MAP = {
    "tunde": "voices/tunde.wav",
    "ngozi": "voices/ngozi.wav",
    "john": "voices/john.wav",
    # add the rest of the 13 personas here as you get their reference clips
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL
    print(f"Loading WazobiaVoice on {DEVICE} ...")
    MODEL = WazobiaVoiceMultilingualTTS.from_pretrained(DEVICE)
    print("Model loaded.")
    yield
    MODEL = None


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    text: str
    language_id: str = "pcm"       # pcm = Nigerian Pidgin
    voice: Optional[str] = None    # one of VOICE_MAP's keys, e.g. "tunde"
    exaggeration: float = 0.5
    cfg_weight: float = 0.5


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": MODEL is not None, "device": DEVICE}


@app.post("/generate")
def generate(data: GenerateRequest):
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model is still loading, try again shortly.")

    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    audio_prompt_path = None
    if data.voice:
        key = data.voice.strip().lower()
        if key not in VOICE_MAP:
            raise HTTPException(status_code=400, detail=f"Unknown voice '{data.voice}'. Known: {list(VOICE_MAP)}")
        path = VOICE_MAP[key]
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail=f"Reference clip missing on server: {path}")
        audio_prompt_path = path

    try:
        wav = MODEL.generate(
            data.text,
            language_id=data.language_id,
            audio_prompt_path=audio_prompt_path,
            exaggeration=data.exaggeration,
            cfg_weight=data.cfg_weight,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.wav")
    ta.save(out_path, wav, MODEL.sr)

    return FileResponse(out_path, media_type="audio/wav", filename="speech.wav")
