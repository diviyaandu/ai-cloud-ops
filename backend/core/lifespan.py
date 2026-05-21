import asyncio
import logging
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI

log = logging.getLogger("cloud-ops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed psutil so the first /metrics call returns real data, not 0.0
    psutil.cpu_percent(interval=None)
    await asyncio.sleep(0.1)
    log.info("psutil warmed up — Groq fires only on demand or significant metric shifts")
    yield