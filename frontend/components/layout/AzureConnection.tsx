"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  connectAzureSession,
  disconnectAzureSession,
  fetchAzureSessionStatus,
  type AzureConnectPayload,
  type AzureSessionStatus,
} from "@/services/api";

type Props = {
  onStatusChange?: (status: AzureSessionStatus) => void;
};

const emptyForm: AzureConnectPayload = {
  subscription_id: "",
  tenant_id: "",
  client_id: "",
  client_secret: "",
};

export default function AzureConnection({ onStatusChange }: Props) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<AzureSessionStatus | null>(null);
  const [form, setForm] = useState<AzureConnectPayload>(emptyForm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const errorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback;

  const refreshStatus = useCallback(() => {
    fetchAzureSessionStatus()
      .then((next) => {
        setStatus(next);
        onStatusChange?.(next);
      })
      .catch((e) => setError(e.message));
  }, [onStatusChange]);

  useEffect(() => {
    refreshStatus();
    const id = setInterval(refreshStatus, 30_000);
    return () => clearInterval(id);
  }, [refreshStatus]);

  const subscription = status?.subscription_id || "Not connected";
  const source =
    status?.source === "session"
      ? "Session"
      : status?.source === "env"
        ? "Env"
        : "None";

  const update = (key: keyof AzureConnectPayload, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const connect = async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await connectAzureSession(form);
      setStatus(next);
      onStatusChange?.(next);
      setForm(emptyForm);
      setOpen(false);
    } catch (e: unknown) {
      setError(errorMessage(e, "Connection failed"));
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await disconnectAzureSession();
      setStatus(next);
      onStatusChange?.(next);
    } catch (e: unknown) {
      setError(errorMessage(e, "Disconnect failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button className="azure-conn-trigger" onClick={() => setOpen(true)}>
        <span>Azure</span>
        <b>{subscription}</b>
      </button>

      {open &&
        createPortal(
          <div className="modal-backdrop" role="presentation">
            <section className="azure-modal" role="dialog" aria-modal="true">
              <div className="azure-modal-head">
                <div>
                  <div className="azure-modal-title">Azure Connection</div>
                  <div className="azure-modal-sub">
                    {source} credentials{" "}
                    {status?.expires_at
                      ? `until ${new Date(status.expires_at).toLocaleString()}`
                      : ""}
                  </div>
                </div>
                <button
                  className="icon-btn"
                  onClick={() => setOpen(false)}
                  aria-label="Close"
                >
                  x
                </button>
              </div>

              <div className="azure-current">
                <span>Current subscription</span>
                <b>{subscription}</b>
              </div>

              <div className="azure-form">
                <input
                  placeholder="subscription_id"
                  value={form.subscription_id}
                  onChange={(e) => update("subscription_id", e.target.value)}
                />
                <input
                  placeholder="tenant_id"
                  value={form.tenant_id}
                  onChange={(e) => update("tenant_id", e.target.value)}
                />
                <input
                  placeholder="client_id"
                  value={form.client_id}
                  onChange={(e) => update("client_id", e.target.value)}
                />
                <input
                  placeholder="client_secret"
                  type="password"
                  value={form.client_secret}
                  onChange={(e) => update("client_secret", e.target.value)}
                />
              </div>

              {error && <div className="azure-error">{error}</div>}

              <div className="azure-actions">
                <button
                  onClick={disconnect}
                  disabled={busy || status?.source !== "session"}
                >
                  Disconnect
                </button>
                <button className="primary" onClick={connect} disabled={busy}>
                  {busy ? "Working..." : "Connect"}
                </button>
              </div>
            </section>
          </div>,
          document.body,
        )}
    </>
  );
}
