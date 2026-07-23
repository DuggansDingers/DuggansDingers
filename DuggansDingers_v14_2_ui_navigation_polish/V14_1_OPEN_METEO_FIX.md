# v14.1 Open-Meteo request fix

- Uses one multi-stadium Open-Meteo request per live slate instead of one request per game.
- Never retries an HTTP 429 immediately.
- Applies a 15-minute provider backoff after a failed/rate-limited request.
- Reuses the last successful forecast during a temporary rate limit.
- Refreshes weather every 30 minutes independently from the slower two-hour model cache.
- Avoids the previous optional-field retry that could double the request count.
