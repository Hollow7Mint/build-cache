"""Build Cache — Entry repository."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BuildWorker:
    """Thin repository wrapper for Entry persistence in Build Cache."""

    TABLE = "entrys"

    def __init__(self, db: Any) -> None:
        self._db = db
        logger.debug("BuildWorker bound to %s", db)

    def insert(self, stored_at: Any, expires_at: Any, **kwargs: Any) -> str:
        """Persist a new Entry row and return its generated ID."""
        rec_id = str(uuid.uuid4())
        row: Dict[str, Any] = {
            "id":         rec_id,
            "stored_at": stored_at,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._db.insert(self.TABLE, row)
        return rec_id

    def fetch(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """Return the Entry row for *rec_id*, or None."""
        return self._db.fetch(self.TABLE, rec_id)

    def update(self, rec_id: str, **fields: Any) -> bool:
        """Patch *fields* on an existing Entry row."""
        if not self._db.exists(self.TABLE, rec_id):
            return False
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._db.update(self.TABLE, rec_id, fields)
        return True

    def delete(self, rec_id: str) -> bool:
        """Hard-delete a Entry row; returns False if not found."""
        if not self._db.exists(self.TABLE, rec_id):
            return False
        self._db.delete(self.TABLE, rec_id)
        return True

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit:    int = 100,
        offset:   int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Return (rows, total_count) for the given *filters*."""
        rows  = self._db.select(self.TABLE, filters or {}, limit, offset)
        total = self._db.count(self.TABLE, filters or {})
        logger.debug("query entrys: %d/%d", len(rows), total)
        return rows, total

    def store_by_key(
        self, value: Any, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch entrys filtered by *key*."""
        rows, _ = self.query({"key": value}, limit=limit)
        return rows

    def bulk_insert(
        self, records: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert *records* in bulk and return their generated IDs."""
        ids: List[str] = []
        for rec in records:
            rec_id = self.insert(
                rec["stored_at"], rec.get("expires_at"),
                **{k: v for k, v in rec.items() if k not in ("stored_at", "expires_at")}
            )
            ids.append(rec_id)
        logger.info("bulk_insert entrys: %d rows", len(ids))
        return ids
