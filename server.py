from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import subprocess
import threading
import uvicorn
import httpx

shiny_process = None
MAPTILER_API_KEY = "OCVJ6l477kLTb0IRr0k5"  # Replace with your key

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Shiny when FastAPI starts
    def run_shiny():
        global shiny_process
        shiny_process = subprocess.Popen([
            "shiny", "run", 
            "--port", "8001",
            "./shiny_app/app.py"  # Your Shiny app file
        ])
    
    threading.Thread(target=run_shiny, daemon=True).start()
    yield
    # Cleanup on shutdown
    if shiny_process:
        shiny_process.terminate()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        # You can pass variables to template here
        "shiny_url": "http://localhost:8001"  
    })

@app.get("/api/geocode")
async def geocode(q: str):
    """Proxy geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{q}.json",
                params={"key": MAPTILER_API_KEY, "limit": 5}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/reverse-geocode")
async def reverse_geocode(lng: float, lat: float):
    """Proxy reverse geocoding requests to MapTiler API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.maptiler.com/geocoding/{lng},{lat}.json",
                params={"key": MAPTILER_API_KEY}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=400, detail=str(e))
        


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)