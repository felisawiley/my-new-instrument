# your-first-memory — the steps, in class order

*Sibling of the Twilight instrument in `twilight_mcp/`. Same shape: read it,
deploy it, make it yours. The server keeps state, and the state lives
somewhere that outlives both the server and the chat.*

## 1. Read the server (3 minutes, really)

[`server.py`](server.py), top to bottom. Notice:

- the schema (8 lines) — the only data design in this folder
- the two tools — record and list, nothing else ([docs/adr/0004](docs/adr/0004-two-tools-and-an-eight-line-schema.md) says why)
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

- *"Record this: …"* — something you want to keep.
- *"What quotes do I have?"*
- Now the real test: **start a brand-new conversation** and ask again.
  The Twilight instrument couldn't do that. This one can.

## 5. Make it yours

`quotes` is a placeholder for *whatever you would actually keep*.
Rename the table, the columns, the tools — the model adapts to your tool
names instantly. When you make a real design choice (add delete? soft or
hard? — see ADR-0004), write your own ADR-0005 in [docs/adr/](docs/adr/).
