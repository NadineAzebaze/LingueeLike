from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Absolute path to templates directory
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Page d'accueil → search.html
@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

# --- Routes API existantes ---
from app.api.dictionary import router as dictionary_router
app.include_router(dictionary_router)