"""twilight diary — a memory for the lines that actually landed.

`twilight_quote()` can hand out a random line forever. It cannot remember
which ones you kept, or what you said back. This table can. See docs/adr/
for every choice — ADR-0005 is the one that makes this diary yours.
"""
import os
from mcp.server.fastmcp import FastMCP

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

mcp = FastMCP(
    "twilight-diary",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS twilight_diary (
    id             SERIAL PRIMARY KEY,
    line           TEXT NOT NULL,
    speaker        TEXT,                       -- optional: unattributed lines are allowed (ADR-0004)
    reaction       TEXT,                       -- the catch; null only on rows copied from quotes
    reacted_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    taken_back_at  TIMESTAMPTZ                 -- soft delete: the row stays (ADR-0005)
);
"""

COPY_FROM_QUOTES = """
INSERT INTO twilight_diary (line, speaker, reacted_at)
SELECT q.quote, q.who, q.recorded_at
FROM quotes q
WHERE NOT EXISTS (
    SELECT 1 FROM twilight_diary d
    WHERE d.line = q.quote
      AND d.reacted_at = q.recorded_at
      AND d.speaker IS NOT DISTINCT FROM q.who
)
"""


def db():
    """One connection per tool call (ADR-0002): Neon's free tier suspends
    when idle, and a fresh connection wakes it transparently. A held pool
    would die during the nap and greet you with a stale-connection error."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Not an error in the code — a feature "
            "waiting for setup: create a free database at neon.tech, copy the "
            "connection string, and set it as an environment variable "
            "(COURSE-STEPS.md, step 2)."
        )
    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'quotes'
            )
            """
        )
        if cur.fetchone()[0]:
            cur.execute(COPY_FROM_QUOTES)
    conn.commit()
    return conn


def _format_entry(entry_id, line, speaker, reaction, reacted_at, taken_back_at, *, show_taken_back):
    stamp = f"{reacted_at:%Y-%m-%d %H:%M}"
    mark = " [taken back]" if taken_back_at and show_taken_back else ""
    who = f"{speaker}: " if speaker else ""
    feeling = f" → {reaction}" if reaction else ""
    return f'#{entry_id} ({stamp}){mark} {who}"{line}"{feeling}'


@mcp.tool()
def react_to_line(line: str, reaction: str, speaker: str = "") -> str:
    """Keep a Twilight line and what it did to you.

    `speaker` is optional — a line you can't place is still worth a reaction.
    `reaction` is the memory: team edward, unhinged, funny, tender, whatever
    the line actually did.
    """
    line = line.strip()
    reaction = reaction.strip()
    if not line:
        raise ValueError("A diary entry needs the line.")
    if not reaction:
        raise ValueError(
            "A diary entry needs a reaction. The line is the excuse; "
            "the reaction is what this diary keeps."
        )
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twilight_diary (line, speaker, reaction)
            VALUES (%s, %s, %s)
            RETURNING id, reacted_at
            """,
            (line, speaker.strip() or None, reaction),
        )
        entry_id, ts = cur.fetchone()
        conn.commit()
    return f"Kept as diary entry #{entry_id} at {ts.isoformat()}."


@mcp.tool()
def my_reactions(include_taken_back: bool = False) -> str:
    """Every reaction still in the diary, oldest first.

    Taken-back entries stay in the table but stay quiet unless
    `include_taken_back` is true.
    """
    with db() as conn, conn.cursor() as cur:
        if include_taken_back:
            cur.execute(
                """
                SELECT id, line, speaker, reaction, reacted_at, taken_back_at
                FROM twilight_diary
                ORDER BY id
                """
            )
        else:
            cur.execute(
                """
                SELECT id, line, speaker, reaction, reacted_at, taken_back_at
                FROM twilight_diary
                WHERE taken_back_at IS NULL
                ORDER BY id
                """
            )
        rows = cur.fetchall()
        if rows:
            return "\n".join(
                _format_entry(*row, show_taken_back=include_taken_back) for row in rows
            )
        if include_taken_back:
            return "The diary is empty. Hear a line, then keep what it did to you."
        cur.execute("SELECT COUNT(*) FROM twilight_diary WHERE taken_back_at IS NOT NULL")
        (taken_back,) = cur.fetchone()
    if taken_back:
        return (
            "Every reaction so far has been taken back. "
            "Ask again if you want the crossed-out ones."
        )
    return "The diary is empty. Hear a line, then keep what it did to you."


@mcp.tool()
def take_back(entry_id: int) -> str:
    """Cross a diary entry out. The row stays, so changing your mind is still a record."""
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT taken_back_at FROM twilight_diary WHERE id = %s
            """,
            (entry_id,),
        )
        row = cur.fetchone()
        if row is None:
            return f"No diary entry #{entry_id}."
        if row[0] is not None:
            return f"Entry #{entry_id} was already taken back at {row[0].isoformat()}."
        cur.execute(
            """
            UPDATE twilight_diary
            SET taken_back_at = now()
            WHERE id = %s
            RETURNING taken_back_at
            """,
            (entry_id,),
        )
        (ts,) = cur.fetchone()
        conn.commit()
    return f"Took back entry #{entry_id} at {ts.isoformat()}. The page stays, crossed out."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
