from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os

app = FastAPI()

# Get the backend URL from environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "https://wazobia-ai.onrender.com")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str):
    # Build the target URL
    url = f"{BACKEND_URL}/{path}"
    
    # Get headers (exclude host)
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    
    # Get body for non-GET requests
    body = await request.body() if request.method not in ["GET", "HEAD"] else None
    
    # Make the request to the backend
    response = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=body,
        allow_redirects=False
    )
    
    # Return the response
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )
