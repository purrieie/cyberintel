# CyberIntel

A cybersecurity threat-intelligence pipeline that crawls security news sources, filters articles with AI relevance scoring, displays them on a live dashboard, and generates branded PDF threat advisories on demand.

## Overview

CyberIntel follows links from five major cybersecurity news sites, extracts and cleans article content, filters out anything older than a configurable window or irrelevant to your interests, and streams keepers to a live SOC-style dashboard in real time. Any article can be turned into a C-FALCON-branded multi-section threat advisory PDF using an LLM for analysis.

**Flow:** Scrapy crawler → SQLite → parse/clean → AI relevance filter → FastAPI + live SSE dashboard → on-demand PDF reports

## Sources

- The Hacker News
- BleepingComputer
- SecurityWeek
- Dark Reading
- KrebsOnSecurity

## Stack

- **Crawling:** scrapy, trafilatura
- **Storage:** sqlalchemy, SQLite
- **API / dashboard:** fastapi, uvicorn, server-sent events
- **AI:** Groq (relevance filtering + report analysis) via the OpenAI-compatible API
- **PDF:** reportlab
- **Misc:** httpx, python-dateutil, apscheduler

## Project Structure

```
cyberintel/
├── api/
│   ├── main.py              # FastAPI app, startup hooks
│   ├── events.py            # CrawlEventBus (Scrapy thread -> FastAPI loop bridge)
│   ├── routes/              # articles, crawler, intelligence, reports
│   └── static/dashboard.html
├── config/
│   ├── seeds.py             # crawl sources + allow/deny URL patterns
│   ├── keywords.py          # FAST_TRACK + INTERESTS for relevance filter
│   └── settings.py
├── crawler/
│   ├── engine.py            # CrawlerProcess runner
│   ├── spiders/             # per-source spiders
│   └── pipelines/           # filter, relevance + storage
├── db/
│   ├── models.py            # Article + Report tables
│   └── repository.py        # DB access layer
├── intelligence/
│   ├── relevance_agent.py   # batched relevance + severity judgment
│   ├── groq_client.py       # Groq API wrapper
│   ├── nim_client.py        # report analysis (runs via Groq)
│   └── article_processor.py # article -> analysis -> PDF glue
├── parser/
│   ├── date_filter.py       # age filter with URL-date fallback
│   ├── cleaner.py
│   ├── normalizer.py
│   ├── deduplicator.py
│   └── pipeline.py
└── reports/
    ├── pdf_builder.py        # C-FALCON branded multi-section PDF
    └── assets/               # gramax.png, cfalcon.png
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install scrapy trafilatura sqlalchemy fastapi uvicorn httpx reportlab apscheduler openai python-dateutil python-dotenv
   ```

3. Create a `.env` file in the project root:

   ```
   GROQ_API_KEY=gsk_your_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
   DB_PATH=./cyberintel.db
   MAX_ARTICLE_AGE_DAYS=180
   ```

4. Initialize the database:

   ```bash
   python -c "from db.models import init_db; init_db()"
   ```

## Running

Start the server from the project root:

```bash
uvicorn api.main:app
```

Then open the dashboard at **http://127.0.0.1:8000/dashboard**

> **Do not use `--reload`.** The file watcher restarts the process and kills any running crawl.

### Using the dashboard

- **Start crawl** — begins crawling all five sources; keepers appear live, newest first
- **Stop crawl** — signals the crawler to stop (the server keeps running)
- **Generate PDF** — runs LLM analysis on that article and downloads a branded threat advisory

### Key endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/dashboard` | GET | Live feed UI |
| `/articles/?limit=N` | GET | Stored articles as JSON |
| `/crawl/start` | POST | Begin a crawl |
| `/crawl/stop` | POST | Stop a crawl |
| `/crawl/stream` | GET | SSE event stream |
| `/reports/generate/{id}` | POST | Generate a PDF for an article |

## Configuration

**Article age window** — `MAX_ARTICLE_AGE_DAYS` in `.env`. Articles older than this are dropped. Uses the page date, falling back to a date embedded in the URL.

**Relevance keywords** — `config/keywords.py`:

- `FAST_TRACK` — terms that auto-keep an article and mark it high severity
- `INTERESTS` — topics injected into the AI prompt to steer relevance judgment

**Crawl sources / URL filtering** — `config/seeds.py`. Tighten `deny_patterns` (e.g. `/category/`, `/page/N/`, `/tag/`) to stop archive and index pages being treated as articles.

**Report model** — `GROQ_MODEL` in `.env`. Use a non-reasoning instruct model such as `llama-3.3-70b-versatile`. Reasoning models leak chain-of-thought into the report body.

## How Relevance Filtering Works

Articles are buffered and judged in batches of 15. A keyword fast-track keeps obvious hits immediately; the rest are judged by the LLM, which also assigns each a severity (high / medium / low). The filter is **fail-open**: if the AI call errors or is rate-limited, articles are kept rather than lost.

## PDF Reports

Each report renders only the sections the source article supports (empty sections are skipped) in the C-FALCON house style: navy masthead with GRAMAX and C-FALCON logos, an Intelligence Snapshot table, executive summary, threat-actor profiles, sector-impact and TTP tables, detection and mitigation measures, strategic recommendations, and a disclaimer / classification footer. Output is saved to `output/pdfs/`.

## Notes & Limitations

- **Single process.** The crawler (Scrapy / Twisted reactor) and the API share one process. Avoid generating PDFs mid-crawl — the crawl saturates the process and requests can stall. The reactor also cannot be cleanly restarted in-process, so a stopped crawl may require a server restart before starting again.
- **Rate limits.** The free Groq tier is rate-limited per account. Heavy crawling drains the same quota the PDF analysis uses; if you hit 429s, the relevance filter fail-opens (keeps everything) and PDF analysis returns a placeholder.
- **Database migrations.** SQLAlchemy `create_all` only creates missing tables, not new columns. After a model change, either delete `cyberintel.db` and re-crawl, or run a manual `ALTER TABLE`.

## Troubleshooting

- **Nothing on the dashboard / `stored=0`.** Confirm the DB was initialized and the age window in `.env` isn't too small. Check the terminal for `STORED id=...` lines.
- **Articles drop as "old."** Expected for archive links the crawler follows. The date filter is working; raise `MAX_ARTICLE_AGE_DAYS` if needed.
- **PDF request hangs forever.** A crawl is probably running and blocking the process. Stop the crawl (or restart the server) and generate with no crawl active.
- **PDF report is full of reasoning text.** The configured model is a reasoning model. Switch `GROQ_MODEL` to an instruct model.
- **`429 Too Many Requests`.** Groq quota exhausted. Stop crawling to stop draining it and wait for the window to reset.

## License

Internal project — not currently licensed for redistribution.
