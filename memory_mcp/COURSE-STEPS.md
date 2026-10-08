# your-first-memory — the steps, in class order

*Sibling of the Twilight instrument in `twilight_mcp/`. Same shape: read it,
deploy it, make it yours. The server keeps state, and the state lives
somewhere that outlives both the server and the chat.*

## 1. Read the server (3 minutes, really)

[`server.py`](server.py), top to bottom. Notice:

- the schema — quote, speaker, book, chapter, page, date published, and a taken-back timestamp
- the starter list in `twilight_catalog.json`, which a connection loads onto the shelf
- three tools — shelve, browse, take back ([ADR-0006](docs/adr/0006-a-shelf-card-is-a-citation.md) is the citation; [ADR-0005](docs/adr/0005-a-twilight-diary-with-a-soft-take-back.md) is why the row stays)
- what happens when `DATABASE_URL` is missing (a pointer, not a crash)

## 2. Get your database (neon.tech)

1. https://neon.tech → Sign up (GitHub works; free tier, no card).
2. Create a project — name it anything ("my-memory" is fine).
3. Copy the **connection string** (starts `postgresql://…`). That string
   is a password: it goes ONE place (step 3), never in code or chat.

## 3. Put the connection string on the memory service

Render asks for a `sync: false` secret only the first time a Blueprint is
created. This repo's Blueprint already exists, so syncing it will **not**
ask for `DATABASE_URL`. Add the variable yourself:

1. The `your-first-memory` service has to exist first. It comes from
   [`render.yaml`](../render.yaml) on this branch. If the Blueprint tracks
   `main` and this change is not on `main` yet, merge it, then sync the
   Blueprint. The Twilight service does not read `DATABASE_URL`.
2. Render Dashboard → **your-first-memory** → **Environment**.
3. **Add Environment Variable**. Key: `DATABASE_URL`. Value: the Neon
   connection string from step 2 (it should include `sslmode=require`).
4. Save. Render redeploys that service. The MCP URL is
   `https://<your-memory-service>.onrender.com/mcp`.

Neon's "connect to Render" button can attach the string to a different
service. The memory server only sees a variable on `your-first-memory`.

Locally, from this folder:

```bash
cd memory_mcp
uv run server.py     # port 8000, or whatever PORT is set to
```

## 4. Connect your Claude, and test the claim

Add the connector (Settings → Connectors → same flow as the Twilight server), then:

- *"Shelve this: … Twilight, chapter First Sight, page 12."*
- *"What's on my shelf?"*
- *"Take back #2."*
- Now the real test: **start a brand-new conversation** and ask again.
  The Twilight quote tool couldn't do that. This shelf can.

## 5. The shelf is yours

A card is a citation: the quote, the book, the chapter, the page, and
the date published. Book, chapter, and page can be blank. The five main
books fill the date when you don't. `take_back` still crosses a card out
and leaves the row. That pair of choices is [ADR-0005](docs/adr/0005-a-twilight-diary-with-a-soft-take-back.md)
and [ADR-0006](docs/adr/0006-a-shelf-card-is-a-citation.md).
