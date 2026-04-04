"""
ipfs_client.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – IPFS Integration
─────────────────────────────────────────────────────────────────────────────
Provides distributed storage for large messages and content, reducing on-chain
storage costs. Only CID (Content Identifier) is stored on-chain.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import IPFS client (optional dependency)
try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False
    logger.warning("ipfshttpclient not installed. IPFS features will be disabled.")


class IPFSClient:
    """
    IPFS client wrapper for content storage and retrieval.
    
    Features:
    - Upload content and get CID
    - Pin content to ensure persistence
    - Retrieve content by CID
    - Support for both local daemon and remote gateways
    """

    def __init__(
        self,
        ipfs_host: Optional[str] = None,
        ipfs_port: Optional[int] = None,
        use_gateway: bool = False,
        gateway_url: Optional[str] = None,
    ):
        """
        Initialize IPFS client.
        
        Args:
            ipfs_host: IPFS daemon host (default: from env or localhost)
            ipfs_port: IPFS daemon port (default: from env or 5001)
            use_gateway: Use HTTP gateway instead of local daemon
            gateway_url: Gateway URL for retrieval (default: ipfs.io)
        """
        self.ipfs_host = ipfs_host or os.getenv("IPFS_HOST", "localhost")
        self.ipfs_port = ipfs_port or int(os.getenv("IPFS_PORT", "5001"))
        self.use_gateway = use_gateway
        self.gateway_url = gateway_url or os.getenv("IPFS_GATEWAY", "https://ipfs.io")
        
        self.client = None
        self.enabled = False
        
        if IPFS_AVAILABLE and not use_gateway:
            self._connect()
        elif use_gateway:
            self.enabled = True
            logger.info(f"IPFS client configured for gateway mode: {self.gateway_url}")
        else:
            logger.warning("IPFS client disabled (ipfshttpclient not available)")

    def _connect(self):
        """Connect to IPFS daemon."""
        try:
            self.client = ipfshttpclient.connect(
                f"/ip4/{self.ipfs_host}/tcp/{self.ipfs_port}/http"
            )
            # Test connection
            version = self.client.version()
            self.enabled = True
            logger.info(f"Connected to IPFS daemon: {version}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS daemon: {e}")
            self.enabled = False

    def upload(self, content: str | bytes | dict) -> Optional[str]:
        """
        Upload content to IPFS and return CID.
        
        Args:
            content: Content to upload (str, bytes, or dict for JSON)
            
        Returns:
            CID (Content Identifier) or None if failed
        """
        if not self.enabled or self.client is None:
            logger.warning("IPFS upload failed: client not enabled")
            return None

        try:
            # Convert dict to JSON
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            
            # Convert string to bytes
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Upload to IPFS
            result = self.client.add_bytes(content)
            cid = result
            
            logger.info(f"Uploaded content to IPFS: {cid}")
            return cid
            
        except Exception as e:
            logger.error(f"IPFS upload failed: {e}")
            return None

    def pin(self, cid: str) -> bool:
        """
        Pin content to ensure it persists on IPFS.
        
        Args:
            cid: Content Identifier to pin
            
        Returns:
            True if pinned successfully
        """
        if not self.enabled or self.client is None:
            logger.warning("IPFS pin failed: client not enabled")
            return False

        try:
            self.client.pin.add(cid)
            logger.info(f"Pinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"IPFS pin failed: {e}")
            return False

    def unpin(self, cid: str) -> bool:
        """
        Unpin content from IPFS.
        
        Args:
            cid: Content Identifier to unpin
            
        Returns:
            True if unpinned successfully
        """
        if not self.enabled or self.client is None:
            logger.warning("IPFS unpin failed: client not enabled")
            return False

        try:
            self.client.pin.rm(cid)
            logger.info(f"Unpinned content: {cid}")
            return True
        except Exception as e:
            logger.error(f"IPFS unpin failed: {e}")
            return False

    def get(self, cid: str) -> Optional[bytes]:
        """
        Retrieve content from IPFS by CID.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Content as bytes or None if failed
        """
        if not self.enabled:
            logger.warning("IPFS get failed: client not enabled")
            return None

        try:
            if self.use_gateway:
                # Use HTTP gateway
                import requests
                url = f"{self.gateway_url}/ipfs/{cid}"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.content
            else:
                # Use local daemon
                content = self.client.cat(cid)
                return content
                
        except Exception as e:
            logger.error(f"IPFS get failed for CID {cid}: {e}")
            return None

    def get_json(self, cid: str) -> Optional[dict]:
        """
        Retrieve JSON content from IPFS by CID.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Parsed JSON dict or None if failed
        """
        content = self.get(cid)
        if content is None:
            return None
        
        try:
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to parse JSON from IPFS CID {cid}: {e}")
            return None

    def get_text(self, cid: str) -> Optional[str]:
        """
        Retrieve text content from IPFS by CID.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Text content or None if failed
        """
        content = self.get(cid)
        if content is None:
            return None
        
        try:
            return content.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decode text from IPFS CID {cid}: {e}")
            return None

    def upload_file(self, file_path: str | Path) -> Optional[str]:
        """
        Upload a file to IPFS and return CID.
        
        Args:
            file_path: Path to file
            
        Returns:
            CID or None if failed
        """
        if not self.enabled or self.client is None:
            logger.warning("IPFS file upload failed: client not enabled")
            return None

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            result = self.client.add(str(file_path))
            cid = result['Hash']
            
            logger.info(f"Uploaded file {file_path} to IPFS: {cid}")
            return cid
            
        except Exception as e:
            logger.error(f"IPFS file upload failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if IPFS client is available and enabled."""
        return self.enabled

    def get_stats(self) -> dict:
        """Get IPFS client statistics."""
        stats = {
            "enabled": self.enabled,
            "available": IPFS_AVAILABLE,
            "host": self.ipfs_host,
            "port": self.ipfs_port,
            "use_gateway": self.use_gateway,
            "gateway_url": self.gateway_url,
        }
        
        if self.enabled and self.client and not self.use_gateway:
            try:
                version = self.client.version()
                stats["daemon_version"] = version
                stats["daemon_connected"] = True
            except Exception:
                stats["daemon_connected"] = False
        
        return stats


# Singleton instance
_ipfs_client: Optional[IPFSClient] = None


def get_ipfs_client() -> IPFSClient:
    """Get or create the global IPFS client instance."""
    global _ipfs_client
    if _ipfs_client is None:
        _ipfs_client = IPFSClient()
    return _ipfs_client
