from fastapi import FastAPI
from routers import sessions, models as models_router, doc, analysis, ppt, ppt_analysis, eval, rewrite
from database import engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocPPT NLP Service", version="1.0.0")

app.include_router(sessions.router)
app.include_router(models_router.router)
app.include_router(doc.router)
app.include_router(analysis.router)
app.include_router(ppt.router)
app.include_router(ppt_analysis.router)
app.include_router(eval.router)
app.include_router(rewrite.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
