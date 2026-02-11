from fastapi.templating import Jinja2Templates
from src.core.deps import get_settings

templates = Jinja2Templates(directory="./src/view/templates")

def homepage(request):
    s = get_settings()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "shiny_url": s.shiny_url,
    })
