from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    message: str
    token: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str

@app.get("/")
async def root():
    # Serve frontend HTML
    return FileResponse("static/index.html")

@app.post("/login")
async def login(data: LoginRequest):
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    return LoginResponse(message="Login successful", token="dummy-token-123")

@app.post("/chat")
async def chat(data: ChatRequest):
    return ChatResponse(reply=f"Echo: {data.message}")

@app.get("/health")
async def health():
    return {"status": "ok"}
