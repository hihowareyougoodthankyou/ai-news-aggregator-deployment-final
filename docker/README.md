# Database Setup

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start PostgreSQL container:**
   ```bash
   cd docker
   docker-compose up -d
   ```

3. **Create database tables:**
   ```bash
   python -m app.database.create_tables
   ```

4. **Verify connection:**
   ```bash
   python -m app.run
   ```

5. **Process digest (after scraping articles):**
   ```bash
   # Set GROQ_API_KEY in .env first
   python -m app.processors.digest_processor
   ```

## Database Credentials (default)

- **User:** newsuser
- **Password:** newspass
- **Database:** news_aggregator
- **Port:** 5432
- **Host:** localhost

You can change these in `.env` file or `docker-compose.yml`.

## Stop Database

```bash
cd docker
docker-compose down
```

## View Database Logs

```bash
cd docker
docker-compose logs -f postgres
```
