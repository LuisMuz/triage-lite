# API module

A read-only HTTP API in front of the `api` function, with Lambda proxy integration (payload 2.0).

| Route | Returns |
|---|---|
| `GET /batches` | Latest batches, newest first (`[api] batch_list_limit` in `config/pipeline.toml`) |
| `GET /batches/{id}` | The batch status, totals and report keys |
| `GET /batches/{id}/incidents` | Incidents; `needs_manual=true\|false` filters them |
| `GET /batches/{id}/report?lang=es\|en` | The Markdown report, inline |

API Gateway matches the route, and the function dispatches on `routeKey`, so a route exists in two places: `local.routes` here and `ROUTES` in `src/triagelite/handlers/api.py`.

- **No authentication** (TL-34). The data is synthetic and the API only reads.
- **Stage throttling:** 10 requests per second, burst 20, which bounds what an abuser can cost.
- **Access logs** go to `/aws/apigateway/<prefix>-api` for 14 days: request ID, time, source IP, route, status and latency. Nothing from the response body is logged.
- **Integration timeout** is 11 s, just above the function's 10 s, so a slow call ends as the function's own error.
