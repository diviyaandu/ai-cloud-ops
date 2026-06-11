from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from state import session_store


router = APIRouter(prefix="/session", tags=["session"])


class ConnectRequest(BaseModel):
    subscription_id: str
    tenant_id: str
    client_id: str
    client_secret: str


@router.post("/connect")
def connect(body: ConnectRequest):
    values = body.dict()
    if any(not str(value).strip() for value in values.values()):
        raise HTTPException(400, "All Azure credential fields are required")
    return session_store.connect(**values)


@router.get("/status")
def status():
    return session_store.status()


@router.post("/disconnect")
def disconnect():
    return session_store.disconnect()
