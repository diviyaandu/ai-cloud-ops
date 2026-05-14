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

@app.get("/metrics")
def metrics():
    return {
        "cpu": randint(20, 95),
        "memory": randint(30, 90),
        "disk": randint(40, 85)
    }

@app.get("/health")
def health():
    return {"status": "healthy"}