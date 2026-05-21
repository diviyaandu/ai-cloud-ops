from pydantic import BaseModel
from typing import List


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    text: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class MetricsResponse(BaseModel):
    cpu:      float
    memory:   float
    disk:     float
    alerts:   List[str]
    severity: str


class AnalyzeResponse(MetricsResponse):
    analysis:             str
    analysis_fresh:       bool
    groq_calls_total:     int
    next_auto_in_seconds: int


class ChatResponse(BaseModel):
    response:         str
    groq_calls_total: int