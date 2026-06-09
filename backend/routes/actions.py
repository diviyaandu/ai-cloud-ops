from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from state.action_store import enqueue, get_all, get_one, update_status
from tools import azure_write

router = APIRouter(prefix="/actions", tags=["actions"])

class ActionRequest(BaseModel):
    action_type: str
    params: dict
    proposed_by: str = "agent"

@router.post("")
def queue_action(body: ActionRequest):
    return enqueue(body.action_type, body.params, body.proposed_by)

@router.get("")
def list_actions():
    return get_all()

@router.post("/{action_id}/approve")
def approve_action(action_id: str):
    record = get_one(action_id)
    if not record:
        raise HTTPException(404, "Action not found")
    if record["status"] != "pending":
        raise HTTPException(400, f"Action is '{record['status']}', not pending")
    
    update_status(action_id, "approved")
    try:
        fn = getattr(azure_write, record["action_type"], None)
        if not fn:
            raise ValueError(f"Unknown action_type: {record['action_type']}")
        result = fn(**record["params"])
        return update_status(action_id, "executed", result=result)
    except Exception as e:
        return update_status(action_id, "failed", error=str(e))

@router.post("/{action_id}/reject")
def reject_action(action_id: str):
    record = get_one(action_id)
    if not record:
        raise HTTPException(404, "Action not found")
    if record["status"] != "pending":
        raise HTTPException(400, f"Action is '{record['status']}', not pending")
    return update_status(action_id, "rejected")