# ADR-0007: The quote list lives on the shelf

- Status: accepted
- Date: 2026-10-08
- Deciders: Felisa Wiley

## Context

`twilight_quote()` read 43 lines from `twilight_quotes.json`: a speaker and
a line, nothing else. The shelf, in Neon, was a second list. Two places
to update, and the file could not hold a page.

## Decision

`memory_mcp/twilight_catalog.json` is the starter list. The first
connection loads it into `twilight_shelf`. A card gains `speaker`. Where
a printed quote index gives a book, chapter, or page, the catalog has
it. The five main books still fill `date_published`. Pages that are
blank stay blank.

`twilight_quote()` on both servers draws a random card that has not
been taken back. The old JSON file is gone.

Seeding fills empty fields only. A page or a book already stored on a
live card is left alone. A taken-back card stays taken back. If that
was the only copy, the starter list is shelved again as a new card.

## The road not taken, and why

**Invent the missing pages.** A lot of these lines are movie dialogue
or a shortened sentence. A made-up page is a citation that lies.
`twilightseriestheories.com` is the source for the pages that are
filled (Confessions p. 274, "You are my life now" p. 314, the epilogue
p. 495, the meteor speech p. 514, "Love is irrational" p. 340). Those
numbers move between printings.

**Keep the JSON as what the tool reads.** Then the database and the
file drift apart again.

## Consequences

The Twilight Render service needs the same `DATABASE_URL` as
`your-first-memory`. Without it, `twilight_quote()` has nothing to read.
To add a line with a page, say it to the shelf, or add it to the catalog
and connect again. A catalog edit does not overwrite a citation already
on the card.
