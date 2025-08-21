from app.src.controls import coordinates, map_updates, chat
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Form
from contextlib import asynccontextmanager
import subprocess
import threading
import uvicorn
import os

shiny_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Shiny when FastAPI starts
    def run_shiny():
        global shiny_process
        # Use Render's port assignment for Shiny app
        shiny_port = os.environ.get('PORT', '8001')
        shiny_process = subprocess.Popen([
            "shiny", "run", 
            "--host", "0.0.0.0",
            "--port", shiny_port,
            "./app/view/map.py"  # Your Shiny app file
        ])
    
    threading.Thread(target=run_shiny, daemon=True).start()
    yield
    # Cleanup on shutdown
    if shiny_process:
        shiny_process.terminate()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="./app/view/static"), name="static")

@app.get("/")
async def read_root(request: Request):
    return await map_updates.read_root(request)

@app.get("/shiny-app")
async def shiny_proxy():
    # Redirect to the Shiny app running on the assigned port
    shiny_port = os.environ.get('SHINY_PORT', '8001')
    return RedirectResponse(url=f"http://0.0.0.0:{shiny_port}")

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
    # Use Render's port assignment
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)