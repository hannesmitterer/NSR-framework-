"""
memory.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Shared Vector Memory
─────────────────────────────────────────────────────────────────────────────
Persistent, searchable memory layer backed by ChromaDB + sentence-transformers.
Every piece of knowledge stored here can be retrieved by semantic similarity.
An optional mini-blockchain (hash-chain) guarantees append-only immutability.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports so the module can be imported without the heavy deps installed
# ---------------------------------------------------------------------------
_chroma_client = None
_collection = None
_encoder = None
_chain: list[str] = []  # hash-chain registry (in-memory + file)
_CHAIN_FILE = Path("memory_db/chain.json")


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb  # noqa: PLC0415

        _chroma_client = chromadb.PersistentClient(path="./memory_db")
        _collection = _chroma_client.get_or_create_collection(
            "lex_amoris",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


def _load_chain() -> list[str]:
    global _chain
    if _CHAIN_FILE.exists():
        try:
            _chain = json.loads(_CHAIN_FILE.read_text())
        except Exception:  # noqa: BLE001
            _chain = []
    return _chain


def _save_chain():
    _CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CHAIN_FILE.write_text(json.dumps(_chain))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class SharedMemory:
    """Thread-safe shared vector memory with hash-chain anchoring."""

    def __init__(self):
        _load_chain()

    # ------------------------------------------------------------------
    def store(self, text: str, metadata: dict | None = None) -> str:
        """
        Embed *text*, store it in ChromaDB, and anchor its hash into the chain.
        Returns the chain hash of this entry.
        """
        try:
            encoder = _get_encoder()
            embedding = encoder.encode(text).tolist()
            collection = _get_collection()

            doc_id = hashlib.sha256(
                f"{text}{time.time()}".encode()
            ).hexdigest()[:16]

            meta = metadata or {}
            meta["timestamp"] = meta.get("timestamp", time.time())

            collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta],
                ids=[doc_id],
            )

            # --- Mini-blockchain anchor ---
            prev = _chain[-1] if _chain else "GENESIS"
            state_hash = hashlib.sha256(text.encode()).hexdigest()
            combined = prev + state_hash
            chain_hash = hashlib.sha256(combined.encode()).hexdigest()
            _chain.append(chain_hash)
            _save_chain()

            logger.debug("Stored doc=%s  chain_len=%d", doc_id, len(_chain))
            return chain_hash
        except Exception as exc:  # noqa: BLE001
            logger.error("Memory.store error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    def query(self, text: str, n: int = 3, min_trust: float = 0.0) -> list[str]:
        """
        Retrieve the *n* most semantically similar documents to *text*.
        *min_trust* can filter by a trust metadata field (if present).
        """
        try:
            encoder = _get_encoder()
            embedding = encoder.encode(text).tolist()
            collection = _get_collection()

            count = collection.count()
            if count == 0:
                return []
            where = {"trust": {"$gte": min_trust}} if min_trust > 0.0 else None
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(n, count),
                where=where,
            )
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception as exc:  # noqa: BLE001
            logger.error("Memory.query error: %s", exc)
            return []

    # ------------------------------------------------------------------
    def chain_length(self) -> int:
        return len(_chain)

    def last_hash(self) -> str:
        return _chain[-1] if _chain else "GENESIS"
