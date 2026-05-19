from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import psutil
import os

from dotenv import load_dotenv
from groq import Groq

# ----------------------------
# Load Environment Variables
# ----------------------------

load_dotenv()

# ----------------------------
# Groq Client
# ----------------------------

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ----------------------------
# App Setup
# ----------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request Models
# ----------------------------

class ChatRequest(BaseModel):
    message: str

# ----------------------------
# Helper Function
# ----------------------------

def get_system_metrics():

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

    severity = "Low"

    if cpu > 80 or memory > 80:
        severity = "High"

    elif cpu > 60 or memory > 60:
        severity = "Medium"

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "alerts": alerts,
        "severity": severity
    }

# ----------------------------
# Routes
# ----------------------------

@app.get("/")
def home():
    return {
        "message": "AI Cloud Ops Running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/metrics")
def metrics():

    data = get_system_metrics()

    return data

# ----------------------------
# AI Analysis Endpoint
# ----------------------------

@app.get("/analyze")
def analyze():

    data = get_system_metrics()

    summary = f"""
    CPU Usage: {data['cpu']}%
    Memory Usage: {data['memory']}%
    Disk Usage: {data['disk']}%

    Severity: {data['severity']}

    Alerts:
    {data['alerts']}
    """

    prompt = f"""
    You are an AI cloud operations assistant.

    Current system state:

    {summary}

    Give:
    - overall system status
    - main issue
    - recommended action

    Keep response short and operational.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are an expert Site Reliability Engineer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=200
    )

    analysis = response.choices[0].message.content

    return {
        "cpu": data["cpu"],
        "memory": data["memory"],
        "disk": data["disk"],
        "alerts": data["alerts"],
        "severity": data["severity"],
        "analysis": analysis
    }

# ----------------------------
# Chat Endpoint
# ----------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    data = get_system_metrics()

    summary = f"""
    CPU Usage: {data['cpu']}%
    Memory Usage: {data['memory']}%
    Disk Usage: {data['disk']}%

    Severity: {data['severity']}

    Alerts:
    {data['alerts']}
    """

    prompt = f"""
    You are an AI Cloud Operations Assistant.

    Current system state:

    {summary}

    User question:
    {request.message}

    Rules:
    - Maximum 3 bullet points
    - Mention actual metrics
    - Be concise
    - Give practical advice
    - Avoid generic AI explanations
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a senior Site Reliability Engineer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=300
    )

    ai_response = response.choices[0].message.content

    return {
        "response": ai_response
    }