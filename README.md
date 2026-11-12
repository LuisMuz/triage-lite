# TriageLite

Serverless pipeline that turns a CSV of QA incidents (Spanish/English) into classified, deduplicated incidents and a bilingual summary report, using Claude on Amazon Bedrock.

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
