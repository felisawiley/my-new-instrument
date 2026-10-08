# ADR-0006: A shelf card is a citation, not a reaction

- Status: accepted
- Date: 2026-10-08
- Deciders: Felisa Wiley

## Context

ADR-0005 made the memory a diary of reactions, and required the reaction
so the table would not copy `twilight_quote()`. That requirement answered
the wrong question. The thing worth keeping is where the line lives:
the quote, the book, the chapter, the page, and the date the book was
published. A reaction is a feeling. A citation is how you find the line
again after the chat is gone.

## Decision

Table `twilight_shelf`. One card holds:

- `quote` — required
- `book`, `chapter`, `page` — optional, blank when you don't have them
- `date_published` — optional; for Twilight, New Moon, Eclipse, Breaking
  Dawn, and Midnight Sun it fills from the original US publication date
  when left blank, and a date you pass in wins
- `shelved_at`, `taken_back_at` — `take_back` is still the soft delete
  from ADR-0005

Tools: `shelve_quote`, `browse_shelf`, `take_back`.

Rows already in `quotes` or `twilight_diary` are copied forward as the
quote and the time. Book, chapter, and page stay empty on those cards
rather than being invented. The old tables stay.

## The road not taken, and why

**Keep the required reaction.** It made the column do a job the quote
file doesn't. It also refused a line you simply wanted to locate later.
Finding the page is the job.

**Require every citation field.** A card that demands a page you don't
remember trains you to type one. Same reason ADR-0004 left `who` nullable.

**Look the page up from the quote text.** The 43 lines in
`twilight_quotes.json` have no page numbers. Guessing one would put a
lie on the shelf.

## Consequences

- Known books carry their hardcover dates: Twilight 2005-10-05, New Moon
  2006-08-21, Eclipse 2007-08-07, Breaking Dawn 2008-08-02, Midnight Sun
  2020-08-04. A paperback wants its own date passed in.
- `react_to_line` and `my_reactions` are gone. The model follows
  `shelve_quote` and `browse_shelf`.
