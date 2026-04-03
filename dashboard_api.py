"""
dashboard_api.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Public REST + WebSocket API / Dashboard Backend
─────────────────────────────────────────────────────────────────────────────
Provides:
  GET  /state           – current snapshot (messages, reputation, memory)
  POST /message         – inject a message into the network
  POST /reputation      – manually update a node reputation
  POST /memory          – add a text entry to shared memory
  GET  /reputation/all  – all reputation scores
  GET  /chain           – hash-chain length & last hash
  WS   /ws              – real-time push of live events

All REST endpoints are open (CORS *); add authentication before production.
"""

from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
import time
from typing import Any

import requests as http_requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [API] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lex Amoris Network API",
    description=(
        "Public REST + WebSocket API for the Lex Amoris multi-agent "
        "cooperative AI ecosystem (Kosymbiosis)."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory state (mirrors what the hub is broadcasting)
# ---------------------------------------------------------------------------
STATE: dict[str, Any] = {
    "messages": collections.deque(maxlen=200),   # last 200 messages
    "reputation": {},                             # {node_id: score}
    "memory": collections.deque(maxlen=100),      # last 100 stored texts
    "chain": {"length": 0, "last_hash": "GENESIS"},
}

# Connected dashboard WebSocket clients
_ws_clients: set[WebSocket] = set()


async def _push_to_clients(data: dict):
    """Broadcast *data* to all connected WebSocket dashboard clients."""
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_json(data)
        except Exception:  # noqa: BLE001
            dead.add(ws)
    _ws_clients -= dead


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MessageIn(BaseModel):
    role: str
    data: str
    node_id: str | None = None


class ReputationUpdate(BaseModel):
    node_id: str
    score: float


class MemoryEntry(BaseModel):
    text: str
    role: str | None = None
    trust: float | None = 0.5


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/state", summary="Current network snapshot")
def get_state():
    return {
        "messages": list(STATE["messages"]),
        "reputation": STATE["reputation"],
        "memory": list(STATE["memory"]),
        "chain": STATE["chain"],
    }


@app.get("/reputation/all", summary="All reputation scores")
def get_all_reputation():
    return {"reputation": STATE["reputation"]}


@app.get("/chain", summary="Hash-chain status")
def get_chain():
    return STATE["chain"]


@app.post("/message", summary="Inject a message into the network")
async def add_message(msg: MessageIn):
    entry = {
        "role": msg.role,
        "data": msg.data,
        "node_id": msg.node_id or "external",
        "timestamp": time.time(),
        "type": "injected",
    }
    STATE["messages"].append(entry)  # deque auto-evicts

    # Forward to the WebSocket hub (best-effort)
    hub_uri = os.getenv("HUB_URI", "ws://hub:8765")
    try:
        import websockets  # noqa: PLC0415

        async with websockets.connect(hub_uri) as ws:
            await ws.send(json.dumps(entry))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not forward message to hub: %s", exc)

    await _push_to_clients({"type": "message", "payload": entry})
    return {"ok": True, "entry": entry}


@app.post("/reputation", summary="Manually update a node reputation score")
async def update_reputation(data: ReputationUpdate):
    score = max(0.0, min(1.0, data.score))
    STATE["reputation"][data.node_id] = score
    await _push_to_clients({"type": "reputation", "payload": STATE["reputation"]})
    return {"ok": True, "node_id": data.node_id, "score": score}


@app.post("/memory", summary="Add a text entry to shared memory")
async def add_memory(entry: MemoryEntry):
    mem_item = {
        "text": entry.text,
        "role": entry.role,
        "trust": entry.trust,
        "timestamp": time.time(),
    }
    STATE["memory"].append(mem_item)  # deque auto-evicts
    await _push_to_clients({"type": "memory", "payload": mem_item})
    return {"ok": True}


# ---------------------------------------------------------------------------
# WebSocket endpoint (real-time dashboard push)
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    logger.info("Dashboard WS client connected (total=%d)", len(_ws_clients))

    # Send current state as initial snapshot
    try:
        await websocket.send_json({
            "type": "snapshot",
            "payload": {
                "messages": list(STATE["messages"]),
                "reputation": STATE["reputation"],
                "memory": list(STATE["memory"]),
                "chain": STATE["chain"],
            },
        })
        while True:
            # Keep the connection alive; clients are passive receivers
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        pass
    finally:
        _ws_clients.discard(websocket)
        logger.info("Dashboard WS client disconnected")


# ---------------------------------------------------------------------------
# Hub bridge: subscribe to the hub and mirror events into STATE + WS clients
# ---------------------------------------------------------------------------

async def _hub_bridge():
    """Background task: connect to the WebSocket hub and relay events."""
    hub_uri = os.getenv("HUB_URI", "ws://hub:8765") + "/dashboard"
    while True:
        try:
            import websockets  # noqa: PLC0415

            logger.info("Connecting to hub bridge at %s …", hub_uri)
            async with websockets.connect(hub_uri) as ws:
                logger.info("Hub bridge connected.")
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if data.get("type") == "backfill":
                        for m in data.get("messages", []):
                            STATE["messages"].append(m)  # deque auto-evicts
                        continue

                    # Mirror into state
                    STATE["messages"].append(data)  # deque auto-evicts

                    # Update reputation if present
                    node_id = data.get("node_id")
                    rep = data.get("reputation")
                    if node_id and rep is not None:
                        STATE["reputation"][node_id] = rep

                    # Update chain info
                    chain_len = data.get("chain_len")
                    if chain_len is not None:
                        STATE["chain"]["length"] = chain_len

                    await _push_to_clients({"type": "message", "payload": data})

        except Exception as exc:  # noqa: BLE001
            logger.warning("Hub bridge error: %s – retrying in 5 s", exc)
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup():
    asyncio.create_task(_hub_bridge())


# ---------------------------------------------------------------------------
# Serve the React frontend (if built)
# ---------------------------------------------------------------------------

_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend", "build")

if os.path.isdir(_FRONTEND_BUILD):
    app.mount("/app", StaticFiles(directory=_FRONTEND_BUILD, html=True), name="frontend")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    """Minimal HTML fallback if React build is not present."""
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            content = f.read()
    else:
        content = "<h1>Lex Amoris API running – visit /docs</h1>"
    return HTMLResponse(content=content, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dashboard_api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
