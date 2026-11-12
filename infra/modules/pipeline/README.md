# Pipeline module

The Standard state machine that runs one batch, the EventBridge rule that starts it, and the SNS topic for failed batches.

```
CSV in incoming/ ──► EventBridge rule ──► Normalize ──► ClassifyChunks (Map, 3 at a time)
                                                          └─ ClassifyChunk ─┬─ ok
                                                                            └─ any error ─► ChunkFailed (batch continues)
                     Dedupe ──► Summarize ──► Finalize ──► Succeeded
   any state fails ──► MarkFailed ──► Notify (SNS) ──► Failed
```

The definition is `statemachine.asl.json`, rendered with `templatefile()`. It uses JSONata and state variables: `Normalize` stores `$batch` (`batch_id` and `chunk_keys`), and every later stage receives it unchanged. Events and outputs carry only IDs and S3 keys.

## Retries

| States | Errors | Attempts | Backoff |
|---|---|---|---|
| `ClassifyChunk`, `Dedupe`, `Summarize` | `LLMRateLimitError`, `LLMTransientError`, Lambda service errors | 4 | 2 s, doubling, full jitter |
| `Normalize`, `Finalize`, `MarkFailed` | Lambda service errors | 3 | 2 s, doubling, full jitter |

The error names are the Python exception class names in `src/triagelite/domain/errors.py`, so renaming one of those classes is a breaking change here.

## Failures

- **A chunk** that still fails after its retries ends in `ChunkFailed`. Its incidents have no results file, so `summarize` and `finalize` mark them `needs_manual`.
- **Any other state** goes to `MarkFailed`, which sets the batch to `failed` with the reason `<State> failed with <ErrorName>`. Only the error name is passed, never the cause, which can quote incident text.
- **`Normalize`** failing goes straight to `Notify`, because the batch ID isn't known yet. On a bad CSV the handler has already marked the batch failed.
- **`Notify`** publishes the execution name, source key, batch ID, failed state and error name, and the run ends in `Failed`.

## Trigger

The data bucket sends its events to EventBridge (storage module). The rule matches `Object Created` for keys `incoming/*.csv` and passes `{"source_key": "<key>"}`. Its role may only call `states:StartExecution` on this state machine.

To start a run by hand, pass the same input:

```bash
aws stepfunctions start-execution --state-machine-arn <arn> --input '{"source_key": "incoming/sample.csv"}'
```

Runs stop after `execution_timeout_seconds` (1 hour by default), so a stuck batch can't keep retrying paid calls.
