"""twilight shelf — the quotes, and where to find them again.

The old twilight_quotes.json list is loaded into this table. See docs/adr/
— ADR-0006 is the citation, ADR-0005 is why taking one back leaves the row,
ADR-0007 is the move off the JSON file.
"""
import os

from mcp.server.fastmcp import FastMCP

from shelf_db import db, format_card, published_for, random_quote

mcp = FastMCP(
    "twilight-shelf",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)


@mcp.tool()
def shelve_quote(
    quote: str,
    book: str = "",
    chapter: str = "",
    page: int | None = None,
    date_published: str = "",
    speaker: str = "",
) -> str:
    """Save a Twilight quote with where to find it again.

    `book`, `chapter`, `page`, and `speaker` are optional — leave blank
    whatever you don't have. For Twilight, New Moon, Eclipse, Breaking
    Dawn, and Midnight Sun, `date_published` fills in from the original
    US edition when you leave it blank. Pass YYYY-MM-DD to override that.
    """
    quote = quote.strip()
    book = book.strip()
    chapter = chapter.strip()
    speaker = speaker.strip()
    if not quote:
        raise ValueError("A shelf card needs the quote.")
    if page is not None and page < 1:
        raise ValueError("page needs to be a positive number, or left off.")
    published = published_for(book, date_published)
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twilight_shelf
                (quote, speaker, book, chapter, page, date_published)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, shelved_at, date_published
            """,
            (quote, speaker or None, book or None, chapter or None, page, published),
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
            SELECT id, quote, speaker, book, chapter, page, date_published, shelved_at, taken_back_at
            FROM twilight_shelf
            {where}
            ORDER BY id
            """
        )
        rows = cur.fetchall()
        if rows:
            return "\n".join(
                format_card(*row, show_taken_back=include_taken_back) for row in rows
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


@mcp.tool()
def twilight_quote() -> str:
    """A random Twilight line from the shelf, with the citation when we have one."""
    return random_quote()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
