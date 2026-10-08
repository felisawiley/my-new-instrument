"""twilight shelf — a memory for a quote you can find again.

`twilight_quote()` can hand out a random line forever. It cannot tell you
which book, which chapter, or which page. This table can. See docs/adr/
— ADR-0006 is the citation, ADR-0005 is why taking one back leaves the row.
"""
import os
from datetime import date

from mcp.server.fastmcp import FastMCP

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

mcp = FastMCP(
    "twilight-shelf",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

# Original US publication dates. A date you pass in wins, so a paperback
# citation can disagree with the hardcover.
PUBLISHED = {
    "twilight": date(2005, 10, 5),
    "new moon": date(2006, 8, 21),
    "eclipse": date(2007, 8, 7),
    "breaking dawn": date(2008, 8, 2),
    "midnight sun": date(2020, 8, 4),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS twilight_shelf (
    id              SERIAL PRIMARY KEY,
    quote           TEXT NOT NULL,
    book            TEXT,
    chapter         TEXT,
    page            INTEGER,
    date_published  DATE,
    shelved_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    taken_back_at   TIMESTAMPTZ                 -- soft delete: the card stays (ADR-0005)
);
"""

COPY_FROM_DIARY = """
INSERT INTO twilight_shelf (quote, shelved_at, taken_back_at)
SELECT d.line, d.reacted_at, d.taken_back_at
FROM twilight_diary d
WHERE NOT EXISTS (
    SELECT 1 FROM twilight_shelf s
    WHERE s.quote = d.line
      AND s.shelved_at = d.reacted_at
)
"""

COPY_FROM_QUOTES = """
INSERT INTO twilight_shelf (quote, shelved_at)
SELECT q.quote, q.recorded_at
FROM quotes q
WHERE NOT EXISTS (
    SELECT 1 FROM twilight_shelf s
    WHERE s.quote = q.quote
      AND s.shelved_at = q.recorded_at
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
        for table, statement in (
            ("twilight_diary", COPY_FROM_DIARY),
            ("quotes", COPY_FROM_QUOTES),
        ):
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (table,),
            )
            if cur.fetchone()[0]:
                cur.execute(statement)
    conn.commit()
    return conn


def _resolve_published(book: str, given: str) -> date | None:
    given = given.strip()
    if given:
        try:
            return date.fromisoformat(given)
        except ValueError as exc:
            raise ValueError(
                "date_published needs a YYYY-MM-DD, like 2005-10-05."
            ) from exc
    return PUBLISHED.get(book.strip().lower())


def _format_card(card_id, quote, book, chapter, page, published, shelved_at, taken_back_at, *, show_taken_back):
    stamp = f"{shelved_at:%Y-%m-%d %H:%M}"
    mark = " [taken back]" if taken_back_at and show_taken_back else ""
    where = []
    if book:
        where.append(book)
    if chapter:
        where.append(f"chapter {chapter}")
    if page is not None:
        where.append(f"p. {page}")
    if published is not None:
        where.append(f"published {published:%Y-%m-%d}")
    place = f"{' · '.join(where)}: " if where else ""
    return f'#{card_id} (shelved {stamp}){mark} {place}"{quote}"'


@mcp.tool()
def shelve_quote(
    quote: str,
    book: str = "",
    chapter: str = "",
    page: int | None = None,
    date_published: str = "",
) -> str:
    """Save a Twilight quote with where to find it again.

    `book`, `chapter`, and `page` are optional — leave blank whatever you
    don't have. For Twilight, New Moon, Eclipse, Breaking Dawn, and
    Midnight Sun, `date_published` fills in from the original US edition
    when you leave it blank. Pass YYYY-MM-DD to override that.
    """
    quote = quote.strip()
    book = book.strip()
    chapter = chapter.strip()
    if not quote:
        raise ValueError("A shelf card needs the quote.")
    if page is not None and page < 1:
        raise ValueError("page needs to be a positive number, or left off.")
    published = _resolve_published(book, date_published)
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twilight_shelf (quote, book, chapter, page, date_published)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, shelved_at, date_published
            """,
            (quote, book or None, chapter or None, page, published),
        )
        card_id, ts, stored_date = cur.fetchone()
        conn.commit()
    when = f" Published {stored_date:%Y-%m-%d}." if stored_date else ""
    return f"Shelved as card #{card_id} at {ts.isoformat()}.{when}"


@mcp.tool()
def browse_shelf(include_taken_back: bool = False) -> str:
    """Every quote still on the shelf, oldest first.

    Taken-back cards stay in the table and stay quiet unless
    `include_taken_back` is true.
    """
    with db() as conn, conn.cursor() as cur:
        where = "" if include_taken_back else "WHERE taken_back_at IS NULL"
        cur.execute(
            f"""
            SELECT id, quote, book, chapter, page, date_published, shelved_at, taken_back_at
            FROM twilight_shelf
            {where}
            ORDER BY id
            """
        )
        rows = cur.fetchall()
        if rows:
            return "\n".join(
                _format_card(*row, show_taken_back=include_taken_back) for row in rows
            )
        if include_taken_back:
            return "The shelf is empty. Shelve a quote you want to find again."
        cur.execute("SELECT COUNT(*) FROM twilight_shelf WHERE taken_back_at IS NOT NULL")
        (taken_back,) = cur.fetchone()
    if taken_back:
        return "Every card so far has been taken back. Ask again if you want the crossed-out ones."
    return "The shelf is empty. Shelve a quote you want to find again."


@mcp.tool()
def take_back(card_id: int) -> str:
    """Cross a card out. The row stays, so the shelf still remembers you pulled it."""
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT taken_back_at FROM twilight_shelf WHERE id = %s",
            (card_id,),
        )
        row = cur.fetchone()
        if row is None:
            return f"No shelf card #{card_id}."
        if row[0] is not None:
            return f"Card #{card_id} was already taken back at {row[0].isoformat()}."
        cur.execute(
            """
            UPDATE twilight_shelf
            SET taken_back_at = now()
            WHERE id = %s
            RETURNING taken_back_at
            """,
            (card_id,),
        )
        (ts,) = cur.fetchone()
        conn.commit()
    return f"Took back card #{card_id} at {ts.isoformat()}. The card stays, crossed out."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
