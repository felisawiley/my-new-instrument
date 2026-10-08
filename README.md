# my-new-instrument

An MCP server that gives a Claude model senses it doesn't have on its own: a clock, and a source of Twilight quotes. Built from the [CIS 7000](https://www.cis.upenn.edu/) "your-first-instrument" starter (Computationally Assisted Metacognition, Penn, Fall 2026).

## Tools

| Tool | What it does |
|---|---|
| `current_time()` | Returns the current UTC and local time. |
| `seconds_since(iso_timestamp)` | Returns elapsed time since a given ISO timestamp. |
| `twilight_quote()` | Returns a random line from [`twilight_quotes.json`](twilight_mcp/twilight_quotes.json) (43 quotes). |

## Run it locally

```bash
cd twilight_mcp
uv run server.py     # starts the server on port 8000
```

Connect it to the `claude` CLI:

```bash
claude mcp add --transport http first-instrument http://localhost:8000/mcp
```

Then ask Claude something like "What time is it?" or "Give me a Twilight quote."

## Connect to claude.ai (browser)

claude.ai calls from Anthropic's cloud, so it can't reach `localhost` directly — you need a tunnel or a deployment.

**Tunnel (temporary, dies with your terminal):**

```bash
cloudflared tunnel --url http://localhost:8000
```

Add the printed `https://….trycloudflare.com/mcp` URL under claude.ai → Settings → Connectors.

**Deploy to Render (permanent, free tier):**

1. [render.com](https://render.com) → Sign in with GitHub → **New +** → **Blueprint** → select this repo → **Apply**. (`render.yaml` handles the rest.)
2. Copy the resulting `https://….onrender.com` URL.
3. claude.ai → Settings → Connectors → edit `first-instrument` → set the URL to `https://….onrender.com/mcp`.

Free tier note: the instance naps when idle, so the first call after a nap takes ~30s.

## A memory that outlives the chat

[`memory_mcp/`](memory_mcp/) is the sibling server: one Postgres table and two tools (`record_quote`, `list_quotes`). Quotes survive the end of the conversation because they live in Neon, not in the chat window. Setup is [memory_mcp/COURSE-STEPS.md](memory_mcp/COURSE-STEPS.md). Design choices are [memory_mcp/docs/adr/](memory_mcp/docs/adr/).

```bash
cd memory_mcp
uv run server.py     # needs DATABASE_URL; see COURSE-STEPS.md step 2
```

Render does not ask for `DATABASE_URL` on an existing Blueprint. After `your-first-memory` exists, open that service → Environment → add `DATABASE_URL` and paste the Neon connection string. It is not stored in this repo.

## Project layout

- [`twilight_mcp/server.py`](twilight_mcp/server.py) — the clock and Twilight-quote tools.
- [`twilight_mcp/twilight_quotes.json`](twilight_mcp/twilight_quotes.json) — the quote data behind `twilight_quote()`.
- [`memory_mcp/server.py`](memory_mcp/server.py) — the persistent quote memory.
- [`docs/adr/`](docs/adr) — the reasoning behind the Twilight instrument's setup.
- [`memory_mcp/docs/adr/`](memory_mcp/docs/adr/) — the reasoning behind the memory server.
- [`render.yaml`](render.yaml) — Render deployment config.

## License

MPL-2.0, with an additional grant covering work built from this template — see [LICENSE.txt](LICENSE.txt) and [TEMPLATE-GRANT.md](TEMPLATE-GRANT.md).
