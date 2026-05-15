from fastapi import FastAPI
from routers import sessions, models, doc, analysis

app = FastAPI(title="DocPPT NLP Service", version="1.0.0")

app.include_router(sessions.router)
app.include_router(models.router)
app.include_router(doc.router)
app.include_router(analysis.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
