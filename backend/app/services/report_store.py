"""In-memory store for generated RFP reports.

The API layer expects `report_store.reports` to exist.
Using a module-level dict keeps behavior consistent across the app
process for the current runtime.
"""

from __future__ import annotations

from typing import Any, Dict

# session_id -> aggregated report JSON
reports: Dict[str, Dict[str, Any]] = {}

