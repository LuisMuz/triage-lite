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
| Incident | `BATCH#<id>` | `INC#<incident_id>` | Classification, cluster ID, `needs_manual` |
| Cluster | `BATCH#<id>` | `CLUSTER#<cluster_id>` | Canonical ID, member IDs |
| Batch listing | `BATCHES` | `<created_at>#<id>` | Listing fields |

| Read | Query |
|---|---|
| One batch | `GetItem` with `PK=BATCH#<id>`, `SK=META` |
| A batch's incidents | `Query` with `PK=BATCH#<id>` and `SK` beginning with `INC#` |
| A batch's clusters | `Query` with `PK=BATCH#<id>` and `SK` beginning with `CLUSTER#` |
| Batches, newest first | `Query` with `PK=BATCHES` and `ScanIndexForward=false` |

`expires_at` is the TTL attribute, in epoch seconds. Items without it never expire.
