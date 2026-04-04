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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rate_limiter import RateLimiter
from audit_log import get_audit_log, AuditEventType
from ipfs_client import get_ipfs_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [API] %(message)s")
logger = logging.getLogger(__name__)

# Initialize rate limiter, audit log, and IPFS client
rate_limiter = RateLimiter()
audit_log = get_audit_log()
ipfs_client = get_ipfs_client()

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
# Rate limiting middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    # Extract client identifier (IP address or custom header)
    client_id = request.client.host if request.client else "unknown"
    
    # Check custom client ID header if present
    if "X-Client-ID" in request.headers:
        client_id = request.headers["X-Client-ID"]
    
    # Get endpoint path
    endpoint = request.url.path
    
    # Check rate limit
    is_allowed, retry_after = rate_limiter.check_limit(client_id, endpoint)
    
    if not is_allowed:
        # Log rate limit exceeded
        audit_log.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            actor_id=client_id,
            metadata={"endpoint": endpoint, "retry_after": retry_after},
            severity="warning"
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after:.2f} seconds.",
            headers={"Retry-After": str(int(retry_after) if retry_after else 60)}
        )
    
    # Record the request
    rate_limiter.record_request(client_id, endpoint)
    
    # Process request
    response = await call_next(request)
    return response

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
# Rate Limiting Management Endpoints
# ---------------------------------------------------------------------------

class ExemptionRequest(BaseModel):
    client_id: str


class RateLimitRuleUpdate(BaseModel):
    endpoint: str
    max_requests: int
    window_seconds: float


@app.get("/rate-limit/exemptions", summary="Get all exempted clients")
def get_exemptions():
    return {"exemptions": list(rate_limiter.get_exemptions())}


@app.post("/rate-limit/exemption", summary="Add client to exemption list")
async def add_exemption(req: ExemptionRequest):
    rate_limiter.add_exemption(req.client_id)
    audit_log.log_event(
        event_type=AuditEventType.EXEMPTION_GRANTED,
        actor_id="admin",
        target_id=req.client_id,
        metadata={"action": "add_exemption"}
    )
    return {"ok": True, "client_id": req.client_id}


@app.delete("/rate-limit/exemption/{client_id}", summary="Remove client from exemption list")
async def remove_exemption(client_id: str):
    rate_limiter.remove_exemption(client_id)
    audit_log.log_event(
        event_type=AuditEventType.EXEMPTION_REVOKED,
        actor_id="admin",
        target_id=client_id,
        metadata={"action": "remove_exemption"}
    )
    return {"ok": True, "client_id": client_id}


@app.get("/rate-limit/stats/{client_id}", summary="Get rate limit stats for a client")
def get_rate_limit_stats(client_id: str, endpoint: str = "global"):
    stats = rate_limiter.get_stats(client_id, endpoint)
    return stats


@app.post("/rate-limit/rule", summary="Update rate limit rule for endpoint")
async def update_rate_limit_rule(req: RateLimitRuleUpdate):
    from rate_limiter import RateLimitRule
    rule = RateLimitRule(
        max_requests=req.max_requests,
        window_seconds=req.window_seconds,
        endpoint=req.endpoint
    )
    rate_limiter.add_rule(req.endpoint, rule)
    audit_log.log_event(
        event_type=AuditEventType.GOVERNANCE_UPDATE,
        actor_id="admin",
        metadata={
            "action": "update_rate_limit_rule",
            "endpoint": req.endpoint,
            "max_requests": req.max_requests,
            "window_seconds": req.window_seconds
        }
    )
    return {"ok": True, "endpoint": req.endpoint, "rule": req.__dict__}


@app.get("/rate-limit/config", summary="Get current rate limiting configuration")
def get_rate_limit_config():
    return rate_limiter.to_dict()


# ---------------------------------------------------------------------------
# IPFS Endpoints
# ---------------------------------------------------------------------------

class IPFSUploadRequest(BaseModel):
    content: str | dict
    pin: bool = True


@app.post("/ipfs/upload", summary="Upload content to IPFS")
async def upload_to_ipfs(req: IPFSUploadRequest):
    cid = ipfs_client.upload(req.content)
    
    if cid is None:
        audit_log.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            actor_id="system",
            metadata={"action": "ipfs_upload_failed"},
            severity="error"
        )
        raise HTTPException(status_code=503, detail="IPFS upload failed")
    
    # Pin if requested
    if req.pin:
        ipfs_client.pin(cid)
    
    audit_log.log_event(
        event_type=AuditEventType.IPFS_UPLOAD,
        actor_id="api",
        metadata={"cid": cid, "pinned": req.pin}
    )
    
    return {"ok": True, "cid": cid, "pinned": req.pin}


@app.get("/ipfs/{cid}", summary="Retrieve content from IPFS by CID")
async def get_from_ipfs(cid: str):
    content = ipfs_client.get_text(cid)
    
    if content is None:
        audit_log.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            actor_id="system",
            metadata={"action": "ipfs_download_failed", "cid": cid},
            severity="error"
        )
        raise HTTPException(status_code=404, detail="Content not found on IPFS")
    
    audit_log.log_event(
        event_type=AuditEventType.IPFS_DOWNLOAD,
        actor_id="api",
        metadata={"cid": cid}
    )
    
    return {"ok": True, "cid": cid, "content": content}


@app.get("/ipfs/stats", summary="Get IPFS client statistics")
def get_ipfs_stats():
    return ipfs_client.get_stats()


# ---------------------------------------------------------------------------
# Audit Log Endpoints
# ---------------------------------------------------------------------------

@app.get("/audit/recent", summary="Get recent audit events")
def get_recent_audit_events(limit: int = 100):
    events = audit_log.get_recent_events(limit)
    return {
        "events": [event.to_dict() for event in events],
        "count": len(events)
    }


@app.get("/audit/query", summary="Query audit events with filters")
def query_audit_events(
    event_type: str | None = None,
    actor_id: str | None = None,
    severity: str | None = None,
    limit: int = 100
):
    events = audit_log.query_events(
        event_type=event_type,
        actor_id=actor_id,
        severity=severity,
        limit=limit
    )
    return {
        "events": [event.to_dict() for event in events],
        "count": len(events),
        "filters": {
            "event_type": event_type,
            "actor_id": actor_id,
            "severity": severity
        }
    }


@app.get("/audit/verify", summary="Verify audit log hash chain integrity")
def verify_audit_chain():
    is_valid, error = audit_log.verify_chain()
    return {
        "valid": is_valid,
        "error": error,
        "message": "Audit chain is valid" if is_valid else f"Audit chain is broken: {error}"
    }


@app.get("/audit/stats", summary="Get audit log statistics")
def get_audit_stats():
    return audit_log.get_stats()


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
