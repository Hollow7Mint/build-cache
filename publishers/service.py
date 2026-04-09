"""Build Cache — Artifact repository."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BuildService:
    """Thin repository wrapper for Artifact persistence in Build Cache."""

    TABLE = "artifacts"

    def __init__(self, db: Any) -> None:
        self._db = db
        logger.debug("BuildService bound to %s", db)

    def insert(self, size_bytes: Any, artifact_hash: Any, **kwargs: Any) -> str:
        """Persist a new Artifact row and return its generated ID."""
        rec_id = str(uuid.uuid4())
        row: Dict[str, Any] = {
            "id":         rec_id,
            "size_bytes": size_bytes,
            "artifact_hash": artifact_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._db.insert(self.TABLE, row)
        return rec_id

    def fetch(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """Return the Artifact row for *rec_id*, or None."""
        return self._db.fetch(self.TABLE, rec_id)

    def update(self, rec_id: str, **fields: Any) -> bool:
        """Patch *fields* on an existing Artifact row."""
        if not self._db.exists(self.TABLE, rec_id):
            return False
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._db.update(self.TABLE, rec_id, fields)
        return True

    def delete(self, rec_id: str) -> bool:
        """Hard-delete a Artifact row; returns False if not found."""
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
        logger.debug("query artifacts: %d/%d", len(rows), total)
        return rows, total

    def export_by_hit_count(
        self, value: Any, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch artifacts filtered by *hit_count*."""
        rows, _ = self.query({"hit_count": value}, limit=limit)
        return rows

    def bulk_insert(
        self, records: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert *records* in bulk and return their generated IDs."""
        ids: List[str] = []
        for rec in records:
            rec_id = self.insert(
                rec["size_bytes"], rec.get("artifact_hash"),
                **{k: v for k, v in rec.items() if k not in ("size_bytes", "artifact_hash")}
            )
            ids.append(rec_id)
        logger.info("bulk_insert artifacts: %d rows", len(ids))
        return ids
