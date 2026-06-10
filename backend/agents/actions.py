"""
agents/actions.py
Helper for agents to propose write actions into the approval queue.
"""
from state.action_store import enqueue

def propose_action(action_type: str, params: dict, proposed_by: str = "agent") -> dict:
    record = enqueue(action_type, params, proposed_by)
    return {"proposed": True, "action_id": record["id"], "action_type": action_type, "params": params}