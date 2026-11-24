# TriageLite

Serverless pipeline that turns a CSV of QA incidents (Spanish/English) into classified, deduplicated incidents and a bilingual summary report, using Claude on Amazon Bedrock.

## Running locally

The same pipeline runs on your machine without anything deployed. It still calls Bedrock, so you need:

- Python 3.12 and [uv](https://docs.astral.sh/uv/).
- An AWS sign-in through IAM Identity Center for an account that can invoke Claude Haiku 4.5 (the `global.` inference profile) and Titan Text Embeddings V2 in `us-east-1`.

```bash
make install
aws sso login --profile <profile>
export AWS_PROFILE=<profile>
make run
make run CSV=path/to/incidents.csv
uv run triagelite run path/to/incidents.csv --out runs/my-test
```

Run these from the repository root: `config/` and `prompts/` are read from the current directory.

**Input.** A UTF-8 CSV whose header has `external_id`, `title` and `description`. It may also have `steps`, `environment`, `reported_at` and `reporter`. A header with any other column is rejected. A bad row is skipped and listed in `row_errors.jsonl`; the rest of the batch still runs. `data/sample.csv` has 20 incidents.

**Output.** Everything goes to `runs/<batch_id>/`, where the batch id is the file name plus a hash of its content. Running the same file again overwrites that folder.

| File | Contains |
|---|---|
| `report.es.md`, `report.en.md` | The final reports |
| `summary.json` | Totals, model calls, cost, PII redactions, duplicate clusters, and which reports fell back to the template |
| `incidents.jsonl` | Normalized incidents with PII redacted |
| `row_errors.jsonl` | Rejected CSV rows and why |
| `classifications.jsonl` | Category, severity and component per incident, or `needs_manual` with the reason |
| `pairs.jsonl`, `clusters.jsonl` | Candidate duplicate pairs with the judge's verdicts, and the resulting clusters |
| `report_facts.json`, `report_drafts.jsonl` | The numbers the report may use, and the model's drafts before placeholders are filled in |
| `llm_calls.jsonl` | One record per model call: model, prompt version, tokens, cost, latency, attempt, status |
| `vectors.npy`, `vectors.json` | The embeddings used for deduplication |

The sample takes 28 model calls and costs about USD 0.05. Logs are JSON lines on stderr, and incident text is never logged. The command exits with code 1 if the run fails.

**Settings.** These environment variables are optional: `TRIAGELITE_CONFIG_DIR` (default `config`), `TRIAGELITE_PROMPTS_DIR` (default `prompts`), `TRIAGELITE_AWS_REGION` (default `us-east-1`) and `TRIAGELITE_LOG_LEVEL` (default `INFO`). Models, prices, prompt versions and limits live in `config/*.toml`.

**Development.** `make help` lists every target.

| Command | Does | Calls AWS |
|---|---|---|
| `make test` | Unit tests with the coverage gate | No |
| `make lint` | Ruff and mypy `--strict` | No |
| `make check` | Lint and tests, as CI runs them | No |
| `make eval` | Classification eval on the tuning split (`PROMPT=classify/vN`, `REPEAT=n`) | Bedrock; answers are cached |
| `make eval-summarize` | Re-runs only the summary on a local run and counts template fallbacks | Bedrock |
| `make infra-check` | Terraform fmt, validate, tflint and checkov | No |

## Using the deployed demo

**Uploads are not public.** A run starts when a CSV lands in `incoming/` of the data bucket. Only someone with AWS credentials for the account can write there; there is no upload endpoint. Sign in with `aws sso login`, then:

```bash
BUCKET=$(terraform -chdir=infra/envs/demo output -raw data_bucket_name)
aws s3 cp data/sample.csv "s3://$BUCKET/incoming/sample.csv"
```

**Results come from a read-only HTTP API** with no authentication, throttled to 10 requests per second (burst 20). It serves synthetic demo data only.

```bash
API=$(terraform -chdir=infra/envs/demo output -raw api_url)
curl "${API}batches"
curl "${API}batches/<batch_id>"
curl "${API}batches/<batch_id>/incidents?needs_manual=true"
curl "${API}batches/<batch_id>/report?lang=es"
```

| Route | Returns |
|---|---|
| `GET /batches` | The 20 latest batches, newest first |
| `GET /batches/{id}` | Status, totals, cost and report keys; a failed batch has its reason |
| `GET /batches/{id}/incidents` | Incidents with their classification and cluster; `needs_manual=true` or `false` filters them |
| `GET /batches/{id}/report?lang=es\|en` | The Markdown report, inline |

Every error has the same shape: `{"error": {"code": "not_found", "message": "..."}}`. The codes are `bad_request` (400), `not_found` (404, including a report that isn't ready yet) and `internal` (500).

**Monitoring.** A CloudWatch dashboard shows cost per batch, tokens by stage, validation errors, runs and function errors:

```bash
terraform -chdir=infra/envs/demo output -raw dashboard_url
```

Three alarms email the address in `alert_email`: a run failed or timed out, functions raised 3 or more errors in 5 minutes, and model calls cost USD 0.50 or more in 24 hours. Details are in `infra/modules/observability/README.md`.

## Continuous integration

GitHub Actions authenticates to AWS with OIDC. The roles are defined in `infra/bootstrap/ci.tf`.

| Workflow | Runs on | Does | AWS role |
|---|---|---|---|
| `ci.yml` | Every PR and push to `main` | `uv sync --locked`, ruff, mypy `--strict`, pytest with an 85% coverage gate on `domain`, `llm` and `pipeline` | None |
| `plan.yml` | PRs that change infra, code, config or prompts | `make build`, fmt, validate, tflint, checkov, then `terraform plan` for `infra/envs/demo` in the job summary | `triagelite-plan`: read-only, with object, item, log and execution reads denied; plans run with `-lock=false`, so it never writes |
| `eval.yml` | PRs that change prompts, config, `src/triagelite` or `evals`; pushes to `main`; twice a week | Classifies the tuning split 3 times with the configured prompt and compares it with `main`'s latest result (paired bootstrap). Fails on a significant drop in severity macro-F1, a drop of 5 points or more, or a cost increase above 15% | `triagelite-eval`: only `bedrock:InvokeModel` on the configured Claude profiles |

Model responses are cached between runs (`evals/cache`, keyed by prompt, model, taxonomy, input and a hash of the package code), so re-running an unchanged commit is free and a full run costs about USD 0.13. If Bedrock is still throttling after backoff, the harness exits with code 3 and nothing from that chunk is cached. The job retries twice and then fails with a "Bedrock throttled" error, which is not a quality result.

`terraform apply` is never run from CI.
