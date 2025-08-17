from app.src.controls import coordinates, map_updates, chat
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Form
from contextlib import asynccontextmanager
import subprocess
import threading
import uvicorn


shiny_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Shiny when FastAPI starts
    def run_shiny():
        global shiny_process
        shiny_process = subprocess.Popen([
            "shiny", "run", 
            "--port", "8001",
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
    uvicorn.run(app, port=8000)