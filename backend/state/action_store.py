import uuid
from datetime import datetime, timezone
from typing import Literal

actions: dict[str, dict] = {}

Status = Literal["pending", "approved", "rejected", "executed", "failed"]

def enqueue(action_type: str, params: dict, proposed_by: str = "agent") -> dict:
    action_id = str(uuid.uuid4())
    record = {
        "id": action_id,
        "action_type": action_type,
        "params": params,
        "proposed_by": proposed_by,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }
    actions[action_id] = record
    return record

def get_all() -> list[dict]:
    return list(actions.values())

def get_one(action_id: str) -> dict | None:
    return actions.get(action_id)

def update_status(action_id: str, status: Status, result=None, error=None) -> dict | None:
    if action_id not in actions:
        return None
    actions[action_id]["status"] = status
    actions[action_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    actions[action_id]["result"] = result
    actions[action_id]["error"] = error
    return actions[action_id]