# AI News Aggregator

Scrapes AI/tech sources (YouTube, OpenAI, Anthropic), summarizes with LLM, curates by user interests, and sends daily digest emails.

## Start

**1. Database**
```bash
cd docker && docker-compose up -d
```

**2. Run pipeline (one-time)**
```bash
uv run run
```
or
```bash
uv run python -m app.run
```

**3. Run with scheduler (daily at 1:30 PM EST)**
```bash
uv run python -m app.scheduler
```

## GitHub Actions

The workflow runs daily at 1:30 PM EST.

**First time?** See **[docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)** for a step-by-step setup guide.

## Config

Copy `.env.example` to `.env` and set:
- `DATABASE_URL` or Postgres credentials
- `GROQ_API_KEY`
- `SMTP_*` and `EMAIL_RECIPIENT` for digest emails
