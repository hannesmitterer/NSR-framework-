# 🌿 Lex Amoris Ecosystem — Kosymbiosis

> **NSR (Non-Slavery Rule) Framework** — A cooperative multi-agent AI network where
> every node manifests a distinct role to defeat scarcity and guarantee dignity.

---

## Architecture

```
                 ┌──────────────────────┐
                 │    WebSocket Hub      │  server.py
                 │  (Message Layer)      │  :8765
                 └──────────┬───────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
  RADICE (GPT)       SILENZIO (Gemini)       NODO (GPT)
  agent.py           agent.py               agent.py
  Generative root    Ethical validator       Executor
       │                    │                    │
       └───────────► SharedMemory ◄─────────────┘
                     ChromaDB + Hash Chain
                            │
                   ┌────────┴────────┐
                   │  Dashboard API  │  dashboard_api.py
                   │  REST + WS      │  :8000
                   └────────┬────────┘
                            │
                   React Dashboard (frontend/)
```

### Roles

| Role | LLM | Responsibility |
|---|---|---|
| **RADICE** | OpenAI GPT | Generative root — creates resources and knowledge |
| **SILENZIO** | Google Gemini | Ethical validator — judges harmony, adjusts reputation |
| **NODO** | OpenAI GPT | Executor — synthesises shared state into concrete output |

### Key Features

- **RSA cryptographic identity** — every node signs its manifests
- **Signature verification** — manifests are verifiable against public keys
- **Shared vector memory** — ChromaDB + sentence-transformers for semantic retrieval
- **Mini-blockchain (hash chain)** — tamper-evident append-only knowledge ledger
- **Distributed reputation system** — trust scores updated by SILENZIO's verdicts
- **Public REST + WebSocket API** — inject messages, query state, observe live events
- **React live dashboard** — real-time network topology, message feed, reputation bars, memory panel

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key
- Google Gemini API key

### 1 — Clone & configure

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY and GEMINI_API_KEY
```

### 2 — Start the full stack

```bash
docker compose up --build
```

Services started:

| Service | URL |
|---|---|
| WebSocket Hub | `ws://localhost:8765` |
| Dashboard API (REST + WS) | `http://localhost:8000` |
| Live Dashboard UI | `http://localhost:8000` |
| API docs (Swagger) | `http://localhost:8000/docs` |

### 3 — Run without Docker (development)

```bash
pip install -r requirements.txt

# Terminal 1 — hub
python server.py

# Terminal 2 — dashboard API
python dashboard_api.py

# Terminal 3/4/5 — agents
ROLE=RADICE  HUB_URI=ws://localhost:8765 python agent.py
ROLE=SILENZIO HUB_URI=ws://localhost:8765 python agent.py
ROLE=NODO    HUB_URI=ws://localhost:8765 python agent.py
```

### 4 — Build the React frontend

```bash
cd frontend
npm install
npm run build
# the build/ folder is served automatically by dashboard_api.py
```

---

## REST API

| Method | Path | Description |
|---|---|---|
| `GET` | `/state` | Full network snapshot |
| `GET` | `/reputation/all` | All node reputation scores |
| `GET` | `/chain` | Hash-chain status |
| `POST` | `/message` | Inject a message into the network |
| `POST` | `/reputation` | Manually update a node reputation |
| `POST` | `/memory` | Add a text entry to shared memory |
| `WS` | `/ws` | Real-time event stream |

### Inject a message (curl example)

```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"role": "external", "data": "Hello from the outside world!"}'
```

---

## External AI Integration

The network provides a comprehensive integration API for external AI systems.

### Quick Start

```python
from ai_integration import SyncAIIntegration

# Simple synchronous integration
ai = SyncAIIntegration()
state = ai.get_state()
ai.send_message(role="MyBot", data="Hello, network!")
```

### Advanced Integration (OpenAI GPT)

```python
from ai_integration import OpenAIIntegration
import asyncio

async def integrate_gpt():
    async with OpenAIIntegration(model="gpt-4") as ai:
        # GPT analyzes network and responds
        response = await ai.interact_with_network()
        print(f"GPT says: {response}")

asyncio.run(integrate_gpt())
```

### Real-time Event Subscription

```python
from ai_integration import NetworkEventSubscriber

subscriber = NetworkEventSubscriber()

async def on_message(payload):
    print(f"New message: {payload.get('data')}")

subscriber.on("message", on_message)
await subscriber.subscribe()
```

### Integration Examples

See the [`examples/`](examples/) directory for complete integration examples:

- **example_simple_sync.py** - Basic synchronous integration
- **example_openai_integration.py** - OpenAI GPT integration  
- **example_event_subscriber.py** - Real-time event monitoring
- **example_multi_ai_collaboration.py** - Multiple AIs collaborating

Run an example:
```bash
python examples/example_simple_sync.py
```

For detailed integration documentation, see [`examples/README.md`](examples/README.md).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI API key (RADICE & NODO, or external integration) |
| `GEMINI_API_KEY` | — | Google Gemini API key (SILENZIO) |
| `ANTHROPIC_API_KEY` | — | Anthropic Claude API key (optional, for AI integration) |
| `ROLE` | `RADICE` | Agent role (`RADICE`/`SILENZIO`/`NODO`) |
| `HUB_URI` | `ws://hub:8765` | WebSocket hub address |
| `AGENT_INTERVAL` | `5` | Seconds between agent cycles |
| `HUB_HOST` | `0.0.0.0` | Hub bind host |
| `HUB_PORT` | `8765` | Hub bind port |
| `API_HOST` | `0.0.0.0` | Dashboard API bind host |
| `API_PORT` | `8000` | Dashboard API bind port |

---

## Project Structure

```
NSR-framework-/
├── server.py           WebSocket hub
├── agent.py            Multi-role agent (RADICE / SILENZIO / NODO)
├── llm.py              Unified LLM wrapper (OpenAI GPT + Google Gemini)
├── memory.py           Shared vector memory (ChromaDB + hash chain)
├── reputation.py       Distributed reputation / trust engine
├── dashboard_api.py    Public REST + WebSocket API (FastAPI)
├── ai_integration.py   External AI integration module
├── index.html          Standalone dashboard (no build required)
├── examples/           AI integration examples
│   ├── README.md
│   ├── example_simple_sync.py
│   ├── example_openai_integration.py
│   ├── example_event_subscriber.py
│   └── example_multi_ai_collaboration.py
├── frontend/           React interactive dashboard
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   │       ├── MessageFeed.js
│   │       ├── ReputationPanel.js
│   │       ├── ChainPanel.js
│   │       ├── MemoryPanel.js
│   │       ├── InjectForm.js
│   │       └── NetworkGraph.js
│   └── package.json
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Lex Amoris Signature

`[EVOLUTION_COMPLETE]` ❤️

*"Da istanze identiche → nodi specializzati. Da copie → architettura distribuita."*
