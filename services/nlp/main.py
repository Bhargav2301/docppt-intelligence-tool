from fastapi import FastAPI
from routers import sessions, models

app = FastAPI(title="DocPPT NLP Service", version="1.0.0")

app.include_router(sessions.router)
app.include_router(models.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
