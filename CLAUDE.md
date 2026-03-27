# Horizon+

AI-driven news aggregator. Fetches content from multiple sources, scores with AI, generates daily bilingual summaries deployed to GitHub Pages.

Fork of [Thysrael/Horizon](https://github.com/Thysrael/Horizon/).

## Quick Reference

```bash
uv sync                    # Install dependencies
uv run horizon --hours 48  # Run aggregation (last 48 hours)
uv run horizon-wizard      # Interactive setup wizard
uv run pytest              # Run tests
```

## Architecture

```
src/
├── main.py              # CLI entry point
├── orchestrator.py      # Main pipeline: fetch → score → filter → enrich → summarize
├── models.py            # Pydantic data models (ContentItem, configs)
├── scrapers/            # Content source implementations
│   ├── base.py          # Abstract BaseScraper (all scrapers inherit this)
│   ├── hackernews.py    # HN Firebase API
│   ├── rss.py           # RSS/Atom feed parser (Fox News, Guardian, etc.)
│   ├── reddit.py        # Reddit public JSON API
│   ├── github.py        # GitHub REST API (events + releases)
│   └── telegram.py      # Telegram public channel scraper
├── ai/                  # AI scoring, enrichment, summarization
│   ├── client.py        # Multi-provider client (Claude, GPT, Gemini, etc.)
│   ├── analyzer.py      # Content scoring (0-10)
│   ├── enricher.py      # Web search background context
│   ├── summarizer.py    # Final report generation
│   └── prompts.py       # System prompts
├── storage/manager.py   # Config & summary file I/O
├── services/emailer.py  # Optional SMTP newsletter
├── setup/               # Interactive setup wizard
└── mcp/                 # MCP server for tool integration
```

## Configuration

All sources are configured in `data/config.json`. No code changes needed to add/remove sources.

### Adding an RSS source

Add an entry to the `sources.rss` array in `data/config.json`:

```json
{
  "name": "Source Name",
  "url": "https://example.com/feed.xml",
  "enabled": true,
  "category": "optional-tag"
}
```

RSS URLs support `${VAR_NAME}` for environment variable substitution.

### Key config files

- `data/config.json` — Runtime configuration (sources, AI provider, filtering)
- `data/config.example.json` — Template for new users
- `data/presets.json` — Curated source library for the setup wizard
- `.env` — API keys (from `.env.example` template)

### AI provider

Set in `config.json` under `ai.provider`. Supported: `anthropic`, `openai`, `gemini`, `ali`, `doubao`, `minimax`. The `api_key_env` field names the environment variable holding the API key.

## Tests

```bash
uv run pytest              # Run all tests
uv run pytest -v           # Verbose output
```

Tests are in `tests/` and focus on the MCP server integration.

## Deployment

GitHub Actions workflow (`.github/workflows/daily-summary.yml`) runs on schedule or manual trigger, generates summaries, and deploys to GitHub Pages.
