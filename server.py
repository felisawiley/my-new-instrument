"""your-first-instrument — a sense of time for a model that has none.

Why time? Ask your Claude "how long have we been talking?" WITHOUT this
connected. It can only guess: no clock lives in a context window. This
server is the smallest honest fix — and the pattern generalizes to any
instrument you can imagine. See docs/adr/ for every choice made here.
"""
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "your-first-instrument",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

@mcp.tool()
def current_time() -> str:
    """The current date and time (UTC and local)."""
    now = datetime.now(timezone.utc)
    return f"UTC: {now.isoformat()} · local: {datetime.now().isoformat()}"

@mcp.tool()
def seconds_since(iso_timestamp: str) -> str:
    """Seconds elapsed since an ISO timestamp (e.g. '2026-09-10T17:15:00')."""
    then = datetime.fromisoformat(iso_timestamp)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    return f"{delta.total_seconds():.0f} seconds ({delta})"

QUOTES_PATH = Path(__file__).parent / "twilight_quotes.json"

def _load_quotes() -> list[dict]:
    with open(QUOTES_PATH) as f:
        return json.load(f)

@mcp.tool()
def twilight_quote() -> str:
    """A random quote from Twilight."""
    quote = random.choice(_load_quotes())
    return f'{quote["speaker"]}: "{quote["line"]}"'

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
