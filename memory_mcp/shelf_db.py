"""The shelf table, the catalog seed, and a random draw from it.

twilight_quote() and the shelf tools both read this table. The old JSON
list is twilight_catalog.json; connecting loads it in. See ADR-0007.
"""
import json
import os
import random
from datetime import date
from pathlib import Path

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")
CATALOG_PATH = Path(__file__).with_name("twilight_catalog.json")

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
    taken_back_at   TIMESTAMPTZ
)
"""

ADD_SPEAKER = "ALTER TABLE twilight_shelf ADD COLUMN IF NOT EXISTS speaker TEXT"

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


def published_for(book: str, given: str = "") -> date | None:
    given = (given or "").strip()
    if given:
        try:
            return date.fromisoformat(given)
        except ValueError as exc:
            raise ValueError(
                "date_published needs a YYYY-MM-DD, like 2005-10-05."
            ) from exc
    return PUBLISHED.get((book or "").strip().lower())


def _load_catalog() -> list[dict]:
    with CATALOG_PATH.open() as handle:
        return json.load(handle)


def _seed_catalog(cur) -> None:
    """Load the old quote list. Fill blank citation fields. Don't clobber
    a page or a book someone already typed, and don't revive a taken-back card."""
    for item in _load_catalog():
        quote = item["quote"]
        speaker = item.get("speaker") or None
        book = item.get("book") or None
        chapter = item.get("chapter") or None
        page = item.get("page")
        published = published_for(book) if book else None
        cur.execute(
            """
            SELECT id, taken_back_at
            FROM twilight_shelf
            WHERE quote = %s
            ORDER BY id
            """,
            (quote,),
        )
        rows = cur.fetchall()
        live = [row_id for row_id, taken_back in rows if taken_back is None]
        if not live:
            cur.execute(
                """
                INSERT INTO twilight_shelf
                    (quote, speaker, book, chapter, page, date_published)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (quote, speaker, book, chapter, page, published),
            )
            continue
        cur.execute(
            """
            UPDATE twilight_shelf SET
                speaker = COALESCE(speaker, %s),
                book = COALESCE(book, %s),
                chapter = COALESCE(chapter, %s),
                page = COALESCE(page, %s),
                date_published = COALESCE(date_published, %s)
            WHERE id = %s
            """,
            (speaker, book, chapter, page, published, live[0]),
        )


def db():
    """One connection per tool call (ADR-0002): Neon's free tier suspends
    when idle, and a fresh connection wakes it transparently."""
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
        cur.execute(ADD_SPEAKER)
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
        _seed_catalog(cur)
    conn.commit()
    return conn


def format_card(
    card_id,
    quote,
    speaker,
    book,
    chapter,
    page,
    published,
    shelved_at,
    taken_back_at,
    *,
    show_taken_back,
    with_id=True,
):
    who = f"{speaker}: " if speaker else ""
    where = []
    if book:
        where.append(book)
    if chapter:
        where.append(f"chapter {chapter}")
    if page is not None:
        where.append(f"p. {page}")
    if published is not None:
        where.append(f"published {published:%Y-%m-%d}")
    place = f" — {' · '.join(where)}" if where else ""
    mark = " [taken back]" if taken_back_at and show_taken_back else ""
    if with_id:
        stamp = f"{shelved_at:%Y-%m-%d %H:%M}"
        return f'#{card_id} (shelved {stamp}){mark} {who}"{quote}"{place}'
    return f'{who}"{quote}"{place}'


def random_quote() -> str:
    """One card still on the shelf. This is what twilight_quote() used to
    read out of a JSON file."""
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, quote, speaker, book, chapter, page, date_published, shelved_at, taken_back_at
            FROM twilight_shelf
            WHERE taken_back_at IS NULL
            """
        )
        rows = cur.fetchall()
    if not rows:
        return "The shelf is empty. Shelve a quote you want to find again."
    row = random.choice(rows)
    return format_card(*row, show_taken_back=False, with_id=False)
