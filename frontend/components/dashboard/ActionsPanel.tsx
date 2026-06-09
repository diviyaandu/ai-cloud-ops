"use client";
import { useEffect, useState } from "react";

type ActionStatus = "pending" | "approved" | "rejected" | "executed" | "failed";

interface Action {
  id: string;
  action_type: string;
  params: Record<string, unknown>;
  proposed_by: string;
  status: ActionStatus;
  created_at: string;
  result: unknown;
  error: string | null;
}

const STATUS_COLOR: Record<ActionStatus, string> = {
  pending: "#facc15",
  approved: "#60a5fa",
  executed: "#34d399",
  rejected: "#9ca3af",
  failed: "#f87171",
};

export default function ActionsPanel() {
  const [actions, setActions] = useState<Action[]>([]);

  const fetchActions = () =>
    fetch("http://localhost:8000/actions")
      .then((r) => r.json())
      .then(setActions)
      .catch(() => {});

  useEffect(() => {
    fetchActions();
    const id = setInterval(fetchActions, 5000);
    return () => clearInterval(id);
  }, []);

  const act = (id: string, verb: "approve" | "reject") =>
    fetch(`http://localhost:8000/actions/${id}/${verb}`, {
      method: "POST",
    }).then(fetchActions);

  return (
    <div className="panel span-1">
      <p className="panel-title">Pending Actions</p>
      {actions.length === 0 ? (
        <div className="alert-none">
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "#34d399",
              display: "inline-block",
            }}
          />
          No pending actions
        </div>
      ) : (
        actions.map((a) => {
          const c = STATUS_COLOR[a.status];
          return (
            <div
              key={a.id}
              className="alert-item"
              style={{
                borderColor: `${c}40`,
                background: `${c}0a`,
                color: "#9ca3af",
              }}
            >
              <span
                className="alert-dot"
                style={{ background: c, marginTop: 4 }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    color: "#e5e7eb",
                    fontSize: 11,
                    fontWeight: 600,
                    marginBottom: 2,
                  }}
                >
                  {a.action_type}
                  <span style={{ color: c, marginLeft: 8, fontWeight: 400 }}>
                    {a.status}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 10,
                    wordBreak: "break-all",
                    marginBottom: 4,
                  }}
                >
                  {JSON.stringify(a.params)}
                </div>
                {a.error && (
                  <div
                    style={{ fontSize: 10, color: "#f87171", marginBottom: 4 }}
                  >
                    {a.error}
                  </div>
                )}
                {a.status === "pending" && (
                  <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                    <button
                      onClick={() => act(a.id, "approve")}
                      style={{
                        fontSize: 10,
                        padding: "2px 10px",
                        borderRadius: 4,
                        background: "#34d39922",
                        border: "1px solid #34d39966",
                        color: "#34d399",
                        cursor: "pointer",
                      }}
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => act(a.id, "reject")}
                      style={{
                        fontSize: 10,
                        padding: "2px 10px",
                        borderRadius: 4,
                        background: "#f8717122",
                        border: "1px solid #f8717166",
                        color: "#f87171",
                        cursor: "pointer",
                      }}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
