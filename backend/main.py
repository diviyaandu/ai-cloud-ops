from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from random import randint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Cloud Ops Running"}

import psutil

@app.get("/metrics")
def metrics():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

@app.get("/health")
def health():
    return {"status": "healthy"}