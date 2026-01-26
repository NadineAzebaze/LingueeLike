from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API running"}
from app.api.dictionary import router as dictionary_router
app.include_router(dictionary_router)

