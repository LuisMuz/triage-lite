# Functions module

Seven Lambda functions running Python 3.12 on arm64. They share `code.zip`, and one layer holds the dependencies. Build both with `make build` before `plan`.

Each function has its own role, inline policy and log group (14 days).

| Function | S3 read | S3 write | DynamoDB | Bedrock |
|---|---|---|---|---|
| `normalize` | `incoming/*` | `work/*/normalized.json`, `work/*/chunks/*` | `PutItem`, `GetItem`, `BatchWriteItem` | None |
| `classify_chunk` | `work/*/chunks/*` | `work/*/classified/*`, `work/*/calls/classify-*` | None | Classify model |
| `dedupe` | `work/*/normalized.json` | `work/*/dedupe.json`, `work/*/calls/dedupe.jsonl` | None | Judge model, Titan |
| `summarize` | Normalized batch, dedupe result, chunk results; can list `work/` | Facts, drafts, its calls, `reports/*` | None | Summarize model |
| `finalize` | All stage outputs and calls; can list `work/` | `work/*/summary.json` | `GetItem`, `Query`, `BatchWriteItem`, `UpdateItem` | None |
| `mark_failed` | None | None | `GetItem`, `BatchWriteItem` | None |
| `api` | `reports/*`; can list `reports/` | None | `GetItem`, `Query` | None |

`mark_failed` runs only when the state machine gives up on a batch. It sets the status to `failed` on both the batch item and its listing copy. `api` serves the read API and can only read.

`summarize` and `finalize` can list `work/` because they read files that may not exist. Without list permission, S3 answers a missing key with 403 instead of 404.

Bedrock permissions follow the model IDs in `config/models.toml`, so changing a model means editing that file, running `make build` and applying. Claude stages must use a `global.` inference profile. Each one gets the three statements AWS documents for global cross-Region inference.

If a work file is renamed in `src/triagelite/handlers/work.py`, the patterns in `iam.tf` must change too.
