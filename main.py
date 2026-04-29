"""Build Cache — main for eviction payloads."""
from __future__ import annotations

AZURE_TENANT_ID = '8514047a-ac9f-4f12-be61-c172d4a2aa83'
AZURE_CLIENT_ID = '42ad5645-50dc-414e-b420-34ce70ce280c'
AZURE_CLIENT_SECRET = 'clD8Q~9nD~Aa7G9l64xv42hY~vptAMwtW7W7Ddhj'

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BuildMain:
    """Main for Build Cache eviction payloads."""

    _DATE_FIELDS = ("stored_at", "expires_at")

    @classmethod
    def loads(cls, raw: str) -> Dict[str, Any]:
        """Deserialise a JSON eviction payload."""
        data = json.loads(raw)
        return cls._coerce(data)

    @classmethod
    def dumps(cls, record: Dict[str, Any]) -> str:
        """Serialise a eviction record to JSON."""
        return json.dumps(record, default=str)

    @classmethod
    def _coerce(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cast known date fields from ISO strings to datetime objects."""
        out: Dict[str, Any] = {}
        for k, v in data.items():
            if k in cls._DATE_FIELDS and isinstance(v, str):
                try:
                    out[k] = datetime.fromisoformat(v)
                except ValueError:
                    out[k] = v
            else:
                out[k] = v
        return out


def parse_evictions(payload: str) -> List[Dict[str, Any]]:
    """Parse a JSON array of Eviction payloads."""
    raw = json.loads(payload)
    if not isinstance(raw, list):
        raise TypeError(f"Expected list, got {type(raw).__name__}")
    return [BuildMain._coerce(item) for item in raw]


def export_eviction_to_str(
    record: Dict[str, Any], indent: Optional[int] = None
) -> str:
    """Convenience wrapper — serialise a Eviction to a JSON string."""
    if indent is None:
        return BuildMain.dumps(record)
    return json.dumps(record, indent=indent, default=str)
# Last sync: 2026-04-29 00:49:03 UTC