# ADR-0005: A Twilight diary, and taking something back is a soft delete

- Status: superseded by ADR-0006 (the columns). The soft delete stands.
- Date: 2026-10-08
- Deciders: Felisa Wiley

## Context

`quotes` was a placeholder. This repo already has a Twilight instrument:
`twilight_quote()` serves a random line from a static file and then forgets
you heard it. A second quote archive would repeat that toy. The thing worth
keeping is the reaction — team Edward again, unhinged, funny, tender — the
catch of your own mind when a line lands.

ADR-0004 left deletion open on purpose: hard delete (the row is gone) or
soft delete (a timestamp, the record keeps its history).

## Decision

Rename the memory. Table `twilight_diary`. Tools:

- `react_to_line(line, reaction, speaker="")` — `speaker` stays optional
  (ADR-0004). `reaction` is required, because that is the column this
  diary exists to keep.
- `my_reactions(include_taken_back=false)` — the current diary, oldest first.
- `take_back(entry_id)` — soft delete. Sets `taken_back_at`. The row stays.

`my_reactions` hides taken-back rows unless asked. Rows already stored in
the placeholder `quotes` table are copied forward once (line, speaker,
time) and left in place. Nothing already kept is dropped.

## The road not taken, and why

**Keep calling it quotes.** The static tool already does lines. A diary
that only stores the line again is the placeholder with a costume on.

**Hard delete.** Burning the row makes the diary lie about its own past.
The fun of this one is changing your mind: Monday you were team Edward,
Tuesday you took it back, and both facts are still true. A crossed-out
page is a better Twilight memory than a missing page.

**A `mood` enum** (`longing | unhinged | funny | …`). Forcing the feeling
into a list trains you to invent one that fits. Free text, same reason
`speaker` is optional.

## Consequences

- Three tools, not two. The third exists because the delete decision is
  real, not because the diary grew a search box.
- Old `record_quote` / `list_quotes` names are gone. The model follows
  the new names; a connector pointed at this server picks them up on the
  next conversation.
- `quotes` is not dropped. It is a leftover of the placeholder, copied
  from, not consulted by the tools.
