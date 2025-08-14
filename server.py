from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)