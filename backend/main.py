import logging

from fastapi import FastAPI

from core.lifespan    import lifespan
from core.middleware  import register_middleware
#from routes           import metrics_router, analysis_router, chat_router
from routes.metrics import router as metrics_router
from routes.analysis import router as analysis_router
from routes.chat import router as chat_router

# ← ADD: new multi-agent router
from api.agent import router as agent_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Cloud Ops", lifespan=lifespan)

register_middleware(app)

app.include_router(metrics_router)
app.include_router(analysis_router)
app.include_router(chat_router)


@app.get("/")
def home():
    return {"message": "AI Cloud Ops Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}

# ← ADD: agent route
app.include_router(agent_router) 
@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}

from routes.cloud_resources import router as cloud_resources_router
app.include_router(cloud_resources_router)