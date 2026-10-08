# ADR-0008: Speaker is a column on the card

- Status: accepted
- Date: 2026-10-08
- Deciders: Felisa Wiley

## Context

The starter catalog already knew who said each line. The shelf grew a
`speaker` column only through `ALTER TABLE`, and `shelve_quote` listed
that argument last. A new card could land with the name blank, and the
column was easy to miss next to book, chapter, and page.

## Decision

`speaker` is in `CREATE TABLE twilight_shelf`, still nullable, right
after `quote`. `shelve_quote` takes it as the second argument. Browsing
a card and the shelve reply both name the speaker. Databases created
before this change still run `ADD COLUMN IF NOT EXISTS`, because
`CREATE TABLE IF NOT EXISTS` will not alter a table that is already
there. A blank speaker stays blank.

## The road not taken, and why

**Require the speaker.** Same reason ADR-0006 leaves the page optional.
Some lines are narration, or two people, or a movie line with no clean
name. A required speaker trains the model to invent one.

## Consequences

Redeploy `your-first-memory` so Claude sees `speaker` beside the quote.
The catalog seed still fills a null speaker and does not overwrite one
already stored.
