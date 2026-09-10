"""your-first-instrument — a sense of time for a model that has none.

Why time? Ask your Claude "how long have we been talking?" WITHOUT this
connected. It can only guess: no clock lives in a context window. This
server is the smallest honest fix — and the pattern generalizes to any
instrument you can imagine. See docs/adr/ for every choice made here.
"""
import os
import random
from datetime import datetime, timezone
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

TWILIGHT_QUOTES = [
    ("Bella", "And so the lion fell in love with the lamb."),
    ("Edward", "About three things I was absolutely positive. First, Edward was a vampire."),
    ("Edward", "You are my life now."),
    ("Bella", "I'd rather die than be with anyone but you."),
    ("Edward", "I'd rather die than stay away from you."),
    ("Jacob", "I'll be here. It's what I do."),
]

@mcp.tool()
def twilight_quote() -> str:
    """A random quote from Twilight."""
    speaker, line = random.choice(TWILIGHT_QUOTES)
    return f'{speaker}: "{line}"'

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
