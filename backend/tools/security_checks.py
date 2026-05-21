"""
tools/security_checks.py

Security audit tool — no external APIs required.
Uses Python stdlib (subprocess, pathlib, re) + psutil.

Checks:
  1. Open listening ports — flags unexpected ports
  2. Failed SSH login attempts — parses /var/log/auth.log or journald
  3. Suspicious processes — checks for known bad names + unusual resource usage
  4. World-writable files in sensitive directories
  5. Users with UID 0 (root-equivalent accounts)
"""

import re
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

import psutil


# ── Config ─────────────────────────────────────────────────────────────────────

# Ports expected to be open — anything else gets flagged
EXPECTED_PORTS: set[int] = {22, 80, 443, 3000, 8000, 8080, 9090, 9100, 3306, 5432}

# Process name substrings that warrant investigation
SUSPICIOUS_PROCESS_NAMES: list[str] = [
    "ncat", "netcat", "nc", "nmap", "masscan",
    "metasploit", "msfconsole", "msfvenom",
    "mimikatz", "empire", "cobalt",
    "cryptominer", "xmrig", "minergate",
    "reverse_shell", "bind_shell",
]

# Directories to scan for world-writable files
SENSITIVE_DIRS: list[str] = ["/etc", "/usr/bin", "/usr/sbin", "/bin", "/sbin"]


# ── Individual checks ──────────────────────────────────────────────────────────

async def check_open_ports() -> dict[str, Any]:
    """List all listening TCP/UDP ports; flag anything not in EXPECTED_PORTS."""
    loop = asyncio.get_event_loop()
    connections = await loop.run_in_executor(None, lambda: psutil.net_connections(kind="inet"))

    listening = []
    unexpected = []

    for conn in connections:
        if conn.status == "LISTEN" or (conn.type and conn.type.name == "SOCK_DGRAM" and conn.laddr):
            port = conn.laddr.port
            try:
                proc_name = psutil.Process(conn.pid).name() if conn.pid else "unknown"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = "unknown"

            entry = {
                "port": port,
                "pid": conn.pid,
                "process": proc_name,
                "family": conn.family.name if conn.family else "unknown",
            }
            listening.append(entry)

            if port not in EXPECTED_PORTS:
                unexpected.append(entry)

    return {
        "check": "open_ports",
        "total_listening": len(listening),
        "unexpected_ports": unexpected,
        "all_ports": listening,
        "status": "critical" if unexpected else "ok",
        "summary": (
            f"{len(unexpected)} unexpected port(s) open: "
            + ", ".join(str(e["port"]) for e in unexpected)
            if unexpected
            else f"All {len(listening)} open ports are expected"
        ),
    }


async def check_failed_ssh_logins(lookback_hours: int = 24) -> dict[str, Any]:
    """
    Count failed SSH login attempts in the last N hours.
    Tries /var/log/auth.log first, falls back to journalctl.
    """
    failures: list[dict[str, str]] = []
    source = "unknown"
    cutoff = datetime.now() - timedelta(hours=lookback_hours)

    auth_log = Path("/var/log/auth.log")
    if auth_log.exists():
        source = "/var/log/auth.log"
        pattern = re.compile(r"Failed password for (?:invalid user )?(\S+) from ([\d.]+)")
        try:
            with auth_log.open(errors="replace") as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        failures.append({
                            "user": match.group(1),
                            "source_ip": match.group(2),
                            "raw": line.strip()[:120],
                        })
        except PermissionError:
            return {
                "check": "failed_ssh_logins",
                "status": "unknown",
                "summary": "Permission denied reading /var/log/auth.log — run as root",
                "failures": [],
            }
    else:
        # Fallback: journalctl
        source = "journalctl"
        try:
            result = subprocess.run(
                ["journalctl", "-u", "ssh", "--since", f"-{lookback_hours}h", "--no-pager", "-q"],
                capture_output=True, text=True, timeout=10,
            )
            pattern = re.compile(r"Failed password for (?:invalid user )?(\S+) from ([\d.]+)")
            for line in result.stdout.splitlines():
                match = pattern.search(line)
                if match:
                    failures.append({
                        "user": match.group(1),
                        "source_ip": match.group(2),
                        "raw": line.strip()[:120],
                    })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return {
                "check": "failed_ssh_logins",
                "status": "unknown",
                "summary": "Could not read SSH logs — journalctl unavailable",
                "failures": [],
            }

    # Group by IP
    from collections import Counter
    ip_counts = Counter(f["source_ip"] for f in failures)
    top_attackers = [{"ip": ip, "attempts": count} for ip, count in ip_counts.most_common(5)]

    status = "critical" if len(failures) > 100 else "warning" if len(failures) > 10 else "ok"

    return {
        "check": "failed_ssh_logins",
        "lookback_hours": lookback_hours,
        "source": source,
        "total_failures": len(failures),
        "unique_source_ips": len(ip_counts),
        "top_attackers": top_attackers,
        "status": status,
        "summary": (
            f"{len(failures)} failed SSH login attempts in last {lookback_hours}h "
            f"from {len(ip_counts)} unique IPs"
        ),
    }


async def check_suspicious_processes() -> dict[str, Any]:
    """Scan running processes for suspicious names and unusual resource usage."""
    loop = asyncio.get_event_loop()

    def _scan():
        suspicious = []
        high_resource = []
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "cmdline"]):
            try:
                info = proc.info
                name_lower = (info["name"] or "").lower()
                cmdline = " ".join(info.get("cmdline") or []).lower()

                # Check name against known-bad list
                for bad in SUSPICIOUS_PROCESS_NAMES:
                    if bad in name_lower or bad in cmdline:
                        suspicious.append({
                            "pid": info["pid"],
                            "name": info["name"],
                            "user": info["username"],
                            "reason": f"matches suspicious pattern '{bad}'",
                            "cmdline": cmdline[:120],
                        })
                        break

                # Flag processes consuming excessive resources
                cpu = info.get("cpu_percent") or 0
                mem = info.get("memory_percent") or 0
                if cpu > 80 or mem > 50:
                    high_resource.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "user": info["username"],
                        "cpu_percent": round(cpu, 1),
                        "memory_percent": round(mem, 1),
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return suspicious, high_resource

    suspicious, high_resource = await loop.run_in_executor(None, _scan)

    status = "critical" if suspicious else ("warning" if high_resource else "ok")
    return {
        "check": "suspicious_processes",
        "suspicious_by_name": suspicious,
        "high_resource_processes": high_resource[:10],  # cap list
        "status": status,
        "summary": (
            f"{len(suspicious)} suspicious process(es) found"
            if suspicious
            else f"No suspicious processes; {len(high_resource)} high-resource process(es)"
        ),
    }


async def check_root_equivalent_users() -> dict[str, Any]:
    """Find any accounts with UID 0 other than root."""
    etc_passwd = Path("/etc/passwd")
    extra_root = []

    if etc_passwd.exists():
        try:
            for line in etc_passwd.read_text(errors="replace").splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[2] == "0" and parts[0] != "root":
                    extra_root.append({"username": parts[0], "uid": 0, "shell": parts[-1]})
        except PermissionError:
            pass

    return {
        "check": "root_equivalent_users",
        "extra_root_accounts": extra_root,
        "status": "critical" if extra_root else "ok",
        "summary": (
            f"{len(extra_root)} unexpected UID-0 account(s): "
            + ", ".join(a["username"] for a in extra_root)
            if extra_root
            else "Only root has UID 0"
        ),
    }


async def check_world_writable_files() -> dict[str, Any]:
    """Find world-writable files in sensitive directories (non-recursive, fast)."""
    found = []
    for directory in SENSITIVE_DIRS:
        p = Path(directory)
        if not p.exists():
            continue
        try:
            for f in p.iterdir():
                try:
                    mode = f.stat().st_mode
                    if mode & 0o002:  # world-writable bit
                        found.append({"path": str(f), "mode": oct(mode)})
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            continue

    return {
        "check": "world_writable_files",
        "directories_scanned": SENSITIVE_DIRS,
        "world_writable": found[:20],  # cap output
        "total_found": len(found),
        "status": "critical" if found else "ok",
        "summary": (
            f"{len(found)} world-writable file(s) in sensitive directories"
            if found
            else "No world-writable files found in sensitive directories"
        ),
    }


async def run_full_audit() -> dict[str, Any]:
    """Run all security checks concurrently. Used by the Security Agent."""
    ports, ssh, procs, root_users, writable = await asyncio.gather(
        check_open_ports(),
        check_failed_ssh_logins(),
        check_suspicious_processes(),
        check_root_equivalent_users(),
        check_world_writable_files(),
        return_exceptions=True,
    )

    results = {}
    for label, val in [
        ("open_ports", ports),
        ("failed_ssh_logins", ssh),
        ("suspicious_processes", procs),
        ("root_equivalent_users", root_users),
        ("world_writable_files", writable),
    ]:
        results[label] = {"error": str(val)} if isinstance(val, Exception) else val

    # Overall severity = worst of all checks
    statuses = [v.get("status", "ok") for v in results.values() if isinstance(v, dict)]
    if "critical" in statuses:
        overall = "critical"
    elif "warning" in statuses:
        overall = "warning"
    else:
        overall = "ok"

    results["overall_status"] = overall
    results["audit_timestamp"] = datetime.utcnow().isoformat() + "Z"
    return results