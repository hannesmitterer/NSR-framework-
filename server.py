import asyncio
import websockets

clients = set()

async def handler(ws):
    clients.add(ws)
    print("🔌 Client connected")

    try:
        async for message in ws:
            print("📡 Broadcast:", message)

            for c in clients:
                if c != ws:
                    await c.send(message)

    finally:
        clients.remove(ws)
        print("❌ Client disconnected")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🌐 WS Hub live on ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())

"""
server.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – WebSocket Hub
─────────────────────────────────────────────────────────────────────────────
Central message-passing layer.  Every agent connects here; messages received
from one client are broadcast to all other clients.  The server also emits
structured events so the dashboard can subscribe and receive live updates.
"""

import asyncio
import collections
import json
import logging
import time
import os

import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HUB] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State shared by the hub (in-memory, broadcast to dashboard clients)
# ---------------------------------------------------------------------------
clients: set[WebSocketServerProtocol] = set()
dashboard_clients: set[WebSocketServerProtocol] = set()
message_log: collections.deque = collections.deque(maxlen=500)


async def _broadcast(payload: dict, sender: WebSocketServerProtocol | None = None):
    """Send *payload* as JSON to every connected client except *sender*."""
    text = json.dumps(payload)
    targets = [c for c in clients if c is not sender]
    if targets:
        await asyncio.gather(*(c.send(text) for c in targets), return_exceptions=True)

    # Also push to dashboard subscribers
    dash_targets = list(dashboard_clients)
    if dash_targets:
        await asyncio.gather(*(c.send(text) for c in dash_targets), return_exceptions=True)


async def handler(ws: WebSocketServerProtocol):
    """Handle one WebSocket connection."""
    path = getattr(ws, "path", "/")

    if path == "/dashboard":
        dashboard_clients.add(ws)
        logger.info("Dashboard client connected (total=%d)", len(dashboard_clients))
        # Send current log backfill
        if message_log:
            await ws.send(json.dumps({"type": "backfill", "messages": message_log[-50:]}))
        try:
            async for _ in ws:
                pass  # dashboard is receive-only
        finally:
            dashboard_clients.discard(ws)
            logger.info("Dashboard client disconnected")
        return

    # Regular agent connection
    clients.add(ws)
    logger.info("Agent connected (total=%d)", len(clients))
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            # Stamp and log
            data.setdefault("timestamp", time.time())
            message_log.append(data)  # deque auto-evicts oldest when full

            logger.info(
                "MSG  role=%-10s  type=%s",
                data.get("role", "?"),
                data.get("type", "data"),
            )

            await _broadcast(data, sender=ws)
    finally:
        clients.discard(ws)
        logger.info("Agent disconnected (remaining=%d)", len(clients))


async def main():
    host = os.getenv("HUB_HOST", "0.0.0.0")
    port = int(os.getenv("HUB_PORT", "8765"))
    logger.info("Starting WebSocket hub on ws://%s:%d", host, port)
    async with websockets.serve(handler, host, port):
        logger.info("Hub is live – waiting for agents …")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
