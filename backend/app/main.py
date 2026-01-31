from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Dossier des templates HTML
templates = Jinja2Templates(directory="app/templates")

# Page d'accueil API
@app.get("/")
def root():
    return {"message": "API running"}

# --- Interface utilisateur ---
@app.get("/ui/search")
def ui_search(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

# --- Routes API existantes ---
from app.api.dictionary import router as dictionary_router
app.include_router(dictionary_router)