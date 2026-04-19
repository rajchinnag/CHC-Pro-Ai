"""CMS LCD/NCD metadata refresh (scheduled, monthly).

For MVP we record a refresh heartbeat in MongoDB + a handful of dataset
counts. Actual policy-text ingestion is out of scope for this sprint.
The public CMS LCD/NCD catalogue is reachable at `data.cms.gov`.
"""
from __future__ import annotations
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import requests

logger = logging.getLogger("chcpro.cms")

# Public CMS data endpoints (metadata only).
_DATASETS = [
    {"id": "lcd", "name": "Medicare LCD Catalogue", "source": "https://www.cms.gov/medicare-coverage-database/"},
    {"id": "ncd", "name": "Medicare NCD Catalogue", "source": "https://www.cms.gov/medicare-coverage-database/"},
    {"id": "ipps", "name": "Medicare IPPS MS-DRG v41", "source": "https://www.cms.gov/medicare/payment/prospective-payment-systems"},
    {"id": "ncci", "name": "NCCI Edits (Quarterly)", "source": "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits"},
    {"id": "mue",  "name": "Medically Unlikely Edits", "source": "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-medically-unlikely-edits"},
]


async def fetch_status() -> dict[str, Any]:
    """Ping CMS to ensure the catalogue is reachable and record a heartbeat.

    We intentionally don't download full datasets — just a lightweight
    HEAD request per source to confirm availability.
    """
    results = []
    for d in _DATASETS:
        entry = {"id": d["id"], "name": d["name"], "source": d["source"]}
        try:
            r = await asyncio.to_thread(requests.head, d["source"], timeout=5, allow_redirects=True)
            entry["reachable"] = r.ok
            entry["status_code"] = r.status_code
        except Exception as e:
            entry["reachable"] = False
            entry["status_code"] = 0
            entry["error"] = str(e)
        results.append(entry)
    return {
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "datasets": results,
    }


async def save_status(db, status: dict) -> None:
    await db.cms_status.delete_many({})  # keep only latest
    await db.cms_status.insert_one({**status, "id": "current"})


async def get_latest(db) -> dict | None:
    doc = await db.cms_status.find_one({"id": "current"}, {"_id": 0})
    return doc


async def needs_refresh(db) -> bool:
    doc = await get_latest(db)
    if not doc:
        return True
    try:
        dt = datetime.fromisoformat(doc["refreshed_at"])
    except Exception:
        return True
    days = int(os.environ.get("LCD_REFRESH_INTERVAL_DAYS", "30"))
    return datetime.now(timezone.utc) - dt > timedelta(days=days)


async def refresh_loop(db, interval_seconds: int = 24 * 3600) -> None:
    """Background task: refresh once at boot, then daily check against interval."""
    while True:
        try:
            if await needs_refresh(db):
                logger.info("CMS LCD/NCD refresh — fetching dataset metadata…")
                status = await fetch_status()
                await save_status(db, status)
                logger.info("CMS refresh complete. %d datasets tracked.", len(status["datasets"]))
        except Exception as e:
            logger.warning("CMS refresh error: %s", e)
        await asyncio.sleep(interval_seconds)
