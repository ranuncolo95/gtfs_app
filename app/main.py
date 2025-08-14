from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import subprocess
from contextlib import asynccontextmanager
import threading

# Global variable to hold the Shiny process
shiny_process = None

def run_shiny_app():
    """Run the Shiny app in a separate process"""
    global shiny_process
    shiny_process = subprocess.Popen([
        "shiny", "run", 
        "--port", "8001", 
        "--reload", 
        "./shiny_app/app.py"  # Your Shiny app file
    ])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for FastAPI"""
    # Startup code
    threading.Thread(target=run_shiny_app, daemon=True).start()
    yield
    # Shutdown code
    if shiny_process:
        shiny_process.terminate()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    """Redirect to the Shiny app"""
    return RedirectResponse(url="http://localhost:8001")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)