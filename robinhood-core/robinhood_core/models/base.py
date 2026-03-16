from typing import Optional
from datetime import datetime


def coerce_timestamp(ts: Optional[str]) -> Optional[str]:
    """Ensure timestamp is ISO 8601 format."""
    if not ts:
        return None
    # Parse and re-format to ensure consistency
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return ts


def coerce_numeric(value) -> Optional[float]:
    """Coerce string/number to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def coerce_int(value) -> Optional[int]:
    """Coerce string/number to int."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None
