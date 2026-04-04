# SilentBridge Enhancement Documentation

## Overview

This document describes the SilentBridge enhancements implemented for the NSR Framework, providing transparency, resilience, cost efficiency, and governance for the Lex Amoris ecosystem.

## Table of Contents

1. [SignedMessage System](#1-signedmessage-system)
2. [Rate Limiting](#2-rate-limiting)
3. [IPFS Integration](#3-ipfs-integration)
4. [Persistent Audit Trail](#4-persistent-audit-trail)
5. [Whitelist/Exemption Management](#5-whitelistexemption-management)
6. [Smart Contract](#6-smart-contract)
7. [Heartbeat Monitoring](#7-heartbeat-monitoring)
8. [Syntropy Metrics](#8-syntropy-metrics)
9. [API Reference](#9-api-reference)

---

## 1. SignedMessage System

### Purpose
Provides **enhanced transparency** through cryptographically signed messages, enabling verification of sender authenticity without relying solely on IP addresses.

### Features
- RSA-2048 signature generation and verification
- Public key registry for cross-agent verification
- Automatic signature verification on message receipt
- Tamper-proof message content

### Usage

#### Creating a Signed Message
```python
from signed_message import SignedMessageFactory

signed_msg = SignedMessageFactory.create_signed_message(
    sender_id="abc12345",
    sender_role="RADICE",
    content={"data": "my message"},
    private_key=my_private_key,
    message_type="agent_manifest"
)
```

#### Verifying a Signed Message
```python
from signed_message import SignedMessage

msg = SignedMessage.from_json(json_string)
is_valid = msg.verify()  # Returns True/False
```

#### Using the Public Key Registry
```python
from signed_message import PublicKeyRegistry

registry = PublicKeyRegistry()
registry.register_key(sender_id, public_key_pem)
is_valid = registry.verify_message(signed_message)
```

### Integration
- **agent.py**: All agent messages are now signed automatically
- Signature verification happens on message receipt
- Failed verifications are logged to audit trail

---

## 2. Rate Limiting

### Purpose
Provides **operational resilience** by protecting against spam and abuse while allowing emergency exemptions.

### Features
- Per-endpoint rate limits (configurable)
- Per-client rate limits
- Sliding window algorithm
- Whitelist/exemption support
- Configurable cooldown periods

### Default Limits
- `/message`: 30 requests/minute
- `/reputation`: 20 requests/minute
- `/memory`: 50 requests/minute
- `/state`: 60 requests/minute
- Global: 100 requests/minute

### Usage

#### Configuring Rate Limits
```python
from rate_limiter import RateLimiter, RateLimitRule

rate_limiter = RateLimiter()
rate_limiter.add_rule(
    "/custom-endpoint",
    RateLimitRule(max_requests=10, window_seconds=60.0)
)
```

#### Adding Exemptions
```python
rate_limiter.add_exemption("trusted-client-id")
```

#### Checking Rate Limits
```python
is_allowed, retry_after = rate_limiter.check_limit(
    client_id="user123",
    endpoint="/message"
)
```

### API Endpoints
- `GET /rate-limit/exemptions` - List exempted clients
- `POST /rate-limit/exemption` - Add exemption
- `DELETE /rate-limit/exemption/{client_id}` - Remove exemption
- `GET /rate-limit/stats/{client_id}` - Get client stats
- `POST /rate-limit/rule` - Update endpoint rule
- `GET /rate-limit/config` - Get current configuration

---

## 3. IPFS Integration

### Purpose
Provides **cost efficiency** by storing large content off-chain, reducing gas costs and on-chain storage.

### Features
- Upload content to IPFS
- Pin content for persistence
- Retrieve content by CID
- Support for JSON, text, and binary files
- Gateway fallback support

### Setup

#### Install IPFS Daemon (Optional)
```bash
# Download and install IPFS
# See: https://docs.ipfs.io/install/

# Start IPFS daemon
ipfs daemon
```

#### Environment Variables
```bash
IPFS_HOST=localhost
IPFS_PORT=5001
IPFS_GATEWAY=https://ipfs.io
```

### Usage

#### Upload to IPFS
```python
from ipfs_client import get_ipfs_client

ipfs = get_ipfs_client()
cid = ipfs.upload({"data": "large content"})
ipfs.pin(cid)  # Ensure persistence
```

#### Retrieve from IPFS
```python
content = ipfs.get_json(cid)
# or
text = ipfs.get_text(cid)
```

### API Endpoints
- `POST /ipfs/upload` - Upload content
- `GET /ipfs/{cid}` - Retrieve content
- `GET /ipfs/stats` - Get IPFS client stats

### Example API Call
```bash
curl -X POST http://localhost:8000/ipfs/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello IPFS", "pin": true}'

# Response:
# {"ok": true, "cid": "Qm...", "pinned": true}
```

---

## 4. Persistent Audit Trail

### Purpose
Provides **continuous auditing** with immutable, queryable logs for compliance and anomaly detection.

### Features
- JSON Lines (JSONL) format
- Hash chain for immutability
- Daily log rotation
- Query and search capabilities
- Event type classification
- Severity levels

### Event Types
- `message_sent`, `message_received`
- `signature_verified`, `signature_failed`
- `reputation_changed`
- `rate_limit_exceeded`
- `exemption_granted`, `exemption_revoked`
- `ipfs_upload`, `ipfs_download`
- `agent_connected`, `agent_disconnected`
- `heartbeat`
- `emergency_override`
- `governance_update`
- `syntropy_violation`
- `system_error`

### Usage

#### Logging Events
```python
from audit_log import get_audit_log, AuditEventType

audit = get_audit_log()
audit.log_event(
    event_type=AuditEventType.MESSAGE_SENT,
    actor_id="node123",
    metadata={"details": "custom data"},
    severity="info"
)
```

#### Querying Events
```python
events = audit.query_events(
    event_type="message_sent",
    actor_id="node123",
    start_time=time.time() - 3600,  # Last hour
    limit=100
)
```

#### Verifying Chain Integrity
```python
is_valid, error = audit.verify_chain()
```

### API Endpoints
- `GET /audit/recent?limit=100` - Get recent events
- `GET /audit/query` - Query with filters
- `GET /audit/verify` - Verify hash chain
- `GET /audit/stats` - Get statistics

### Log File Location
```
memory_db/audit/audit_2026-04-04.jsonl
```

---

## 5. Whitelist/Exemption Management

### Purpose
Provides **controlled governance** through dynamic access control and emergency overrides.

### Features
- Client whitelist management
- Rate limit exemptions
- Dynamic updates via API
- Audit logging for all changes

### Usage

#### Add to Whitelist
```bash
curl -X POST http://localhost:8000/rate-limit/exemption \
  -H "Content-Type: application/json" \
  -d '{"client_id": "emergency-responder"}'
```

#### Remove from Whitelist
```bash
curl -X DELETE http://localhost:8000/rate-limit/exemption/emergency-responder
```

#### List Exemptions
```bash
curl http://localhost:8000/rate-limit/exemptions
```

---

## 6. Smart Contract

### Purpose
Provides on-chain message registry with CID storage for blockchain-based verification.

### Contract: SilentBridge.sol

#### Features
- Message registration with IPFS CID
- Role-based access control
- Whitelist management
- Rate limiting via cooldown
- Emergency pause mechanism
- Event emissions for audit trail

#### Deployment

```solidity
// Deploy to Optimism L2
SilentBridge bridge = new SilentBridge();

// Add whitelisted addresses
bridge.addToWhitelist(0x1234...);
bridge.addExemption(0x5678...);

// Set cooldown (default: 60 seconds)
bridge.setCooldownPeriod(30);
```

#### Register a Message

```solidity
string memory cid = "QmXxx...";
string memory nodeId = "abc12345";
string memory role = "RADICE";
bytes32 contentHash = keccak256(abi.encodePacked(content));

uint256 messageId = bridge.registerMessage(
    cid,
    nodeId,
    role,
    "agent_manifest",
    contentHash
);
```

#### Events
```solidity
event MessageRegistered(
    uint256 indexed messageId,
    address indexed sender,
    string nodeId,
    string role,
    string cid,
    uint256 timestamp
);

event WhitelistUpdated(address indexed account, bool whitelisted);
event ExemptionUpdated(address indexed account, bool exempted);
event CooldownPeriodUpdated(uint256 oldPeriod, uint256 newPeriod);
```

---

## 7. Heartbeat Monitoring

### Purpose
Provides continuous system health monitoring at target frequency (321.5 Hz).

### Features
- Configurable target frequency
- Real-time frequency calculation
- Anomaly detection
- Statistics collection
- Variance tracking

### Usage

#### Manual Heartbeat Recording
```python
from heartbeat import get_heartbeat_monitor

monitor = get_heartbeat_monitor()
is_normal = monitor.beat()  # Record heartbeat
```

#### Starting Automatic Emission
```python
from heartbeat import HeartbeatEmitter

emitter = HeartbeatEmitter(target_frequency=321.5)
emitter.start()
```

#### Get Statistics
```python
stats = monitor.get_stats()
print(f"Frequency: {stats.average_frequency} Hz")
print(f"Variance: {stats.frequency_variance}")
```

### API Endpoints
- `GET /heartbeat/stats` - Get heartbeat statistics
- `POST /heartbeat/beat` - Record manual heartbeat
- `GET /heartbeat/frequency` - Get current frequency

### Environment Variables
```bash
ENABLE_HEARTBEAT=true
HEARTBEAT_FREQUENCY=321.5
```

---

## 8. Syntropy Metrics

### Purpose
Provides **Urformel alignment** checking by measuring life-nurturing vs parasitic behavior.

### Features
- Message evaluation for syntropy
- Action evaluation
- Entity scoring
- Global health metrics
- Urformel alignment verification

### Behavior Classifications
- **LIFE_NURTURING**: Cooperative, abundant, trust-building
- **NEUTRAL**: Neither beneficial nor harmful
- **PARASITIC**: Competitive, scarce, exploitative
- **UNKNOWN**: Not yet classified

### Usage

#### Evaluate a Message
```python
from syntropy_metrics import get_syntropy_metrics

metrics = get_syntropy_metrics()
score = metrics.evaluate_message(
    sender_id="node123",
    message_content="Let's cooperate and share resources",
    metadata={"verified_signature": True}
)

print(f"Score: {score.value}")  # -1.0 to 1.0
print(f"Type: {score.behavior_type}")
print(f"Reason: {score.reason}")
```

#### Evaluate an Action
```python
score = metrics.evaluate_action(
    actor_id="node123",
    action_type="share_knowledge",
    success=True
)
```

#### Check Urformel Alignment
```python
is_aligned = metrics.is_urformel_aligned(threshold=0.6)
stats = metrics.get_global_stats()
print(f"Health Score: {stats['health_score']}")
```

### API Endpoints
- `POST /syntropy/evaluate/message` - Evaluate message
- `POST /syntropy/evaluate/action` - Evaluate action
- `GET /syntropy/entity/{entity_id}` - Get entity score
- `GET /syntropy/global` - Get global statistics
- `GET /syntropy/health` - Check Urformel alignment

### Evaluation Criteria

**Positive Indicators:**
- Cooperative language
- Abundance mindset
- Information sharing
- Trust building
- Verified signatures

**Negative Indicators:**
- Competitive language
- Scarcity mindset
- Information hoarding
- Trust violations
- Spam/abuse patterns

---

## 9. API Reference

### Complete Endpoint List

#### State & Core
- `GET /state` - Network snapshot
- `POST /message` - Inject message
- `POST /reputation` - Update reputation
- `POST /memory` - Add memory entry
- `GET /reputation/all` - All reputation scores
- `GET /chain` - Hash-chain status

#### Rate Limiting (7 endpoints)
- `GET /rate-limit/exemptions`
- `POST /rate-limit/exemption`
- `DELETE /rate-limit/exemption/{client_id}`
- `GET /rate-limit/stats/{client_id}`
- `POST /rate-limit/rule`
- `GET /rate-limit/config`

#### IPFS (3 endpoints)
- `POST /ipfs/upload`
- `GET /ipfs/{cid}`
- `GET /ipfs/stats`

#### Audit (4 endpoints)
- `GET /audit/recent`
- `GET /audit/query`
- `GET /audit/verify`
- `GET /audit/stats`

#### Heartbeat (3 endpoints)
- `GET /heartbeat/stats`
- `POST /heartbeat/beat`
- `GET /heartbeat/frequency`

#### Syntropy (5 endpoints)
- `POST /syntropy/evaluate/message`
- `POST /syntropy/evaluate/action`
- `GET /syntropy/entity/{entity_id}`
- `GET /syntropy/global`
- `GET /syntropy/health`

#### WebSocket
- `WS /ws` - Real-time dashboard updates

---

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Optional: Install IPFS
```bash
# See https://docs.ipfs.io/install/
ipfs daemon
```

### 3. Environment Configuration
Create `.env` file:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Hub Configuration
HUB_URI=ws://hub:8765

# IPFS Configuration (optional)
IPFS_HOST=localhost
IPFS_PORT=5001
IPFS_GATEWAY=https://ipfs.io

# Heartbeat Configuration (optional)
ENABLE_HEARTBEAT=true
HEARTBEAT_FREQUENCY=321.5

# Agent Configuration
AGENT_INTERVAL=5
SILENZIO_JUDGE_INTERVAL=3
```

### 4. Start Services
```bash
# Start hub
python server.py

# Start API
python dashboard_api.py

# Start agents
ROLE=RADICE python agent.py
ROLE=SILENZIO python agent.py
ROLE=NODO python agent.py
```

---

## Testing

### Run Basic Tests
```bash
# Test rate limiting
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"role": "test", "data": "hello"}'

# Test IPFS (if enabled)
curl -X POST http://localhost:8000/ipfs/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "test data", "pin": true}'

# Test syntropy evaluation
curl -X POST http://localhost:8000/syntropy/evaluate/message \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "test", "message_content": "cooperative sharing"}'

# Check audit trail
curl http://localhost:8000/audit/recent?limit=10
```

---

## Troubleshooting

### IPFS Not Available
If IPFS features are disabled:
- Install IPFS daemon OR
- Set to use gateway mode only
- IPFS features gracefully degrade

### Rate Limit Issues
If requests are blocked:
- Check `/rate-limit/stats/{client_id}`
- Add to exemptions if needed
- Adjust rate limit rules via `/rate-limit/rule`

### Audit Chain Broken
If verification fails:
- Check `/audit/verify` for details
- May occur after service restart
- Hash chain rebuilds automatically

---

## Security Considerations

1. **Authentication**: Add authentication before production (currently CORS *)
2. **Smart Contract**: Deploy with multisig owner for governance
3. **Rate Limits**: Configure based on expected load
4. **IPFS**: Use private IPFS network for sensitive data
5. **Audit Logs**: Protect log files from tampering
6. **Exemptions**: Carefully manage exemption list

---

## Performance Notes

- Rate limiter uses in-memory storage (fast but not persistent)
- Audit logs use daily rotation to manage file size
- IPFS operations are async and non-blocking
- Heartbeat at 321.5 Hz is high-frequency (adjust if needed)
- Syntropy evaluation is lightweight but scales with message volume

---

## Future Enhancements

- [ ] Selective broadcast with topic filtering
- [ ] Persistent storage for rate limits (Redis)
- [ ] Smart contract integration with agents
- [ ] Advanced syntropy ML models
- [ ] Distributed audit log consensus
- [ ] Multi-signature support for messages

---

## Support & Documentation

- **Repository**: https://github.com/hannesmitterer/NSR-framework-
- **API Docs**: http://localhost:8000/docs (when running)
- **Smart Contract**: See `SilentBridge.sol` for full interface

---

**End of Documentation**
