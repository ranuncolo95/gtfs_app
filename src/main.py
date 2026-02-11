from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from src.web.homepage import homepage
from src.web.api_router import api_router
from src.shiny.shiny_app import app as shiny_app


def create_app() -> FastAPI:
    app = FastAPI()

    # Static e template
    app.mount("/static", StaticFiles(directory="./src/view/static"), name="static")

    # Shiny montata dentro FastAPI
    app.mount("/shiny", shiny_app)

    # Web
    @app.get("/")
    def root(request: Request):
        return homepage(request)

    # API
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
