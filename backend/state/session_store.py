import os
from datetime import datetime, timedelta, timezone


_session: dict | None = None
_env_credential = None
SESSION_TTL_SECONDS = int(os.getenv("AZURE_SESSION_TTL_SECONDS", "3600"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _env_subscription_id() -> str:
    return os.getenv("AZURE_SUBSCRIPTION_ID", "")


def _env_has_credentials() -> bool:
    return all(
        os.getenv(name, "")
        for name in (
            "AZURE_SUBSCRIPTION_ID",
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
        )
    )


def connect(
    subscription_id: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> dict:
    from azure.identity import ClientSecretCredential

    global _session
    expires_at = _now() + timedelta(seconds=SESSION_TTL_SECONDS)
    _session = {
        "credential": ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        ),
        "subscription_id": subscription_id,
        "expires_at": expires_at,
    }
    return status()


def disconnect() -> dict:
    global _session
    _session = None
    return status()


def get_session() -> dict | None:
    global _session
    if _session and _session["expires_at"] <= _now():
        _session = None
    return _session


def get_credential():
    global _env_credential
    session = get_session()
    if session:
        return session["credential"]

    if not _env_has_credentials():
        return None

    if _env_credential is None:
        from azure.identity import ClientSecretCredential

        _env_credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID", ""),
            client_id=os.getenv("AZURE_CLIENT_ID", ""),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
        )
    return _env_credential


def get_subscription_id() -> str:
    session = get_session()
    if session:
        return session["subscription_id"]
    return _env_subscription_id()


def status() -> dict:
    session = get_session()
    if session:
        return {
            "connected": True,
            "source": "session",
            "subscription_id": session["subscription_id"],
            "expires_at": session["expires_at"].isoformat(),
        }

    env_subscription_id = _env_subscription_id()
    return {
        "connected": False,
        "source": "env" if _env_has_credentials() else "none",
        "subscription_id": env_subscription_id or None,
        "expires_at": None,
    }
