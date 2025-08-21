import subprocess
import threading
import os
import time
from app.src.controls import coordinates, map_updates, chat
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Form
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="./app/view/static"), name="static")

def run_shiny():
    # Use a different port for Shiny
    shiny_port = os.environ.get('SHINY_PORT', '8001')
    subprocess.run([
        "shiny", "run", 
        "--host", "0.0.0.0",
        "--port", shiny_port,
        "./app/view/map.py"
    ])

# Start Shiny only if not running on Render (for local development)
if os.environ.get("RENDER", "").lower() != "true":
    shiny_thread = threading.Thread(target=run_shiny, daemon=True)
    shiny_thread.start()
    time.sleep(2)  # Give Shiny time to start

@app.get("/")
async def read_root(request: Request):
    return await map_updates.read_root(request)

# In main.py
@app.get("/shiny-app")
async def shiny_proxy():
    # For internal communication
    shiny_url = os.environ.get("SHINY_URL", "http://gtfs-shiny-app:10000")
    return RedirectResponse(url=shiny_url)

@app.get("/api/geocode")
async def geocode_endpoint(q: str):
    result = await coordinates.geocode(q) 
    return result

@app.get("/api/reverse-geocode")
async def reverse_geocode_endpoint(lng: float, lat: float):
    result = await coordinates.reverse_geocode(lng, lat)  
    return result
        

@app.post("/api/calculate-route")
async def calculate_route(request: Request):
    result = await map_updates.calculate_route(request)  
    return result
    

@app.get("/chat-history", response_class=HTMLResponse)
async def get_chat_history():
    result = await chat.get_chat_history()  
    return result

@app.post("/chat")
async def handle_chat(message: str = Form(...)):
    result = await chat.handle_chat(message)  
    return result


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)