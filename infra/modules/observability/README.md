# Observability module

A CloudWatch dashboard, three alarms that email through the pipeline's SNS topic, and three saved Logs Insights queries.

## Metrics

The functions write metrics as [Embedded Metric Format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html) log lines (`src/triagelite/metrics.py`). CloudWatch Logs turns each line into metric data points, so the code makes no API call and needs no IAM permission. The namespace is `TriageLite`, passed to the functions as `TRIAGELITE_METRICS_NAMESPACE`.

| Metric | Written by | One value per |
|---|---|---|
| `InputTokens`, `OutputTokens`, `CostUSD`, `LatencyMs`, `ValidationErrors` | `classify_chunk`, `dedupe`, `summarize` | model call attempt, failed ones included |
| `NeedsManual`, `PIIRedactions` | `finalize` | finished batch |

No metric has dimensions. CloudWatch bills every name and dimension combination as its own metric, so seven names stay seven metrics, inside the 10 free custom metrics. Breakdowns by stage, model or batch come from the same log lines through Logs Insights. Each line keeps `batch_id`, `stage`, `call_id` and `model_id` as plain fields for that.

## Alarms

All three publish to the alerts topic, which also receives the pipeline's own failure message from `Notify`.

| Alarm | Fires when | Why |
|---|---|---|
| `<prefix>-run-failed` | `ExecutionsFailed` + `ExecutionsTimedOut` ≥ 1 in 5 minutes | A timed-out run never reaches `MarkFailed` or `Notify`, so this alarm is its only signal |
| `<prefix>-function-errors` | `Errors` across all seven functions ≥ 3 in 5 minutes | Catches errors Step Functions retried away, and `api` crashes |
| `<prefix>-daily-model-cost` | `CostUSD` ≥ 0.50 over the last 24 hours | TL-08 alert level; one day and one period is not a multi-day alarm, so the window slides |

Missing data counts as not breaching, so an idle pipeline stays `OK`. The alarms use 10 alarm metrics in total (2 + 7 + 1), which is the free-tier limit; another alarm would cost about $0.10 a month (*verify* on the [CloudWatch pricing page](https://aws.amazon.com/cloudwatch/pricing/)).

The topic policy lets only this project's alarms (`<prefix>-*`) in this account publish. Step Functions publishes with its own role's permission.

## Email

Set the address in the gitignored `infra/envs/demo/terraform.tfvars`:

```hcl
alert_email = "you@example.com"
```

After `apply`, AWS sends a confirmation email. Nothing is delivered until the link in it is clicked. A destroy and apply creates a new subscription that needs confirming again.

## Saved queries

They appear in the Logs Insights console under the `<prefix>/` folder, preselected on the `classify_chunk`, `dedupe` and `summarize` log groups. The dashboard shows the same queries as log widgets.

| Query | Shows |
|---|---|
| `slowest-llm-calls` | The 20 slowest model calls with stage, model, prompt version, attempt and tokens |
| `validation-failures-by-stage` | Calls whose output failed validation, by stage and prompt version |
| `cost-by-batch` | Cost, calls and tokens for the 20 latest batches |

Log widgets and saved queries read the logs, which are kept for 14 days. Metric widgets keep their data for 15 months.
