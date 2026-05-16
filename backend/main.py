from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import os

from dotenv import load_dotenv
import ollama

load_dotenv()

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
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    alerts = []

    if cpu > 80:
        alerts.append("High CPU Usage")

    if memory > 80:
        alerts.append("High Memory Usage")

    if disk > 90:
        alerts.append("Disk Almost Full")

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "alerts": alerts
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
@app.get("/analyze")
def analyze():

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    alerts = []

    if cpu > 80:
        alerts.append("High CPU Usage")

    if memory > 80:
        alerts.append("High Memory Usage")

    if disk > 90:
        alerts.append("Disk Almost Full")

    prompt = f"""
    Analyze these system metrics.

    CPU Usage: {cpu}%
    Memory Usage: {memory}%
    Disk Usage: {disk}%

    Active Alerts:
    {alerts}

    Explain:
    - possible issues
    - severity
    - recommended actions
    """

    response = ollama.chat(
        model='tinyllama',
        messages=[
            {
                'role': 'system',
                'content': 'You are an expert cloud operations engineer.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
    )

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "alerts": alerts,
        "analysis": response['message']['content']
    }