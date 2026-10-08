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

## 3. Deploy (render.com — same Blueprint as the Twilight server)

1. Render → this repo's Blueprint (root [`render.yaml`](../render.yaml)).
2. When Render asks for `DATABASE_URL` on the `your-first-memory` service, paste your Neon string.
3. Deploy. The memory MCP URL is `https://<your-memory-service>.onrender.com/mcp`.

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
