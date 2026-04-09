"""Build Cache — Eviction service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BuildRepository:
    """Business-logic service for Eviction operations in Build Cache."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("BuildRepository started")

    def fetch(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the fetch workflow for a new Eviction."""
        if "key" not in payload:
            raise ValueError("Missing required field: key")
        record = self._repo.insert(
            payload["key"], payload.get("expires_at"),
            **{k: v for k, v in payload.items()
              if k not in ("key", "expires_at")}
        )
        if self._events:
            self._events.emit("eviction.fetchd", record)
        return record

    def warm(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Eviction and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Eviction {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("eviction.warmd", updated)
        return updated

    def expire(self, rec_id: str) -> None:
        """Remove a Eviction and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Eviction {rec_id!r} not found")
        if self._events:
            self._events.emit("eviction.expired", {"id": rec_id})

    def search(
        self,
        key: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search evictions by *key* and/or *status*."""
        filters: Dict[str, Any] = {}
        if key is not None:
            filters["key"] = key
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search evictions: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Eviction counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
