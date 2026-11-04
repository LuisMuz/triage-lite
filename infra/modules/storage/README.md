# Storage module

One S3 bucket for files and one DynamoDB table for records.

## Bucket prefixes

| Prefix | Holds | Expiry |
|---|---|---|
| `incoming/` | Uploaded CSVs. An upload here starts a run. | None |
| `work/` | Intermediate files passed between stages. | `work_retention_days` |
| `reports/` | Finished reports. | None |

S3 has no real folders, so a prefix exists once an object uses it.

## DynamoDB keys

| Item | `PK` | `SK` | Attributes |
|---|---|---|---|
| Batch | `BATCH#<id>` | `META` | Status, counts, cost, timestamps, report keys |
| Incident | `BATCH#<id>` | `INC#<incident_id>` | Status, classification or reason, cluster ID, external ID, title, language |
| Cluster | `BATCH#<id>` | `CLUSTER#<cluster_id>` | Canonical ID, member IDs |
| Batch listing | `BATCHES` | `<created_at>#<id>` | Same attributes as the batch item |

`created_at` is UTC and stays the same when a batch is re-run, so a batch has one listing entry.

| Read | Query |
|---|---|
| One batch | `GetItem` with `PK=BATCH#<id>`, `SK=META` |
| A batch's incidents | `Query` with `PK=BATCH#<id>` and `SK` beginning with `INC#` |
| A batch's clusters | `Query` with `PK=BATCH#<id>` and `SK` beginning with `CLUSTER#` |
| Batches, newest first | `Query` with `PK=BATCHES` and `ScanIndexForward=false` |

`expires_at` is the TTL attribute, in epoch seconds. Items without it never expire, and nothing writes it yet.
