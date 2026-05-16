# Security

## Secrets Policy

- Never commit `.env`.
- Never commit API keys, tokens, passwords, cookies, or credentials.
- Use `.env.example` for placeholders only.

## Data Policy

- Do not commit large raw data dumps.
- Do not commit private user data.
- Keep raw data and processed data separated.

## Web Crawling Safety

- Respect robots.txt where applicable.
- Prefer API/RSS/sitemap before HTML scraping.
- Do not bypass CAPTCHA, login, paywall, or access controls.
- Use rate limits, timeouts, and retries.
- Log errors per source instead of crashing the pipeline.

## Human Approval

Human approval is required before:

- destructive commands
- production deployment
- deleting data
- changing database schema in a breaking way
- merging large rewrites
