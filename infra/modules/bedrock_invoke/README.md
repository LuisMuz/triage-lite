# Bedrock invoke module

A policy document that lets a role call `bedrock:InvokeModel` on Claude through the given global cross-Region inference profiles, and nothing else. It has no resources: callers attach `policy_json` to their own role.

It holds the three statements AWS documents for global cross-Region inference:

1. The inference profile in this Region.
2. The foundation model in this Region, only when called through one of the profiles.
3. The foundation model with no Region (`unspecified`), for requests the profile routes to another Region, also only through one of the profiles.

Used by the `classify_chunk`, `dedupe` and `summarize` roles (`modules/functions`) and by the CI eval role (`bootstrap/ci.tf`), so the pipeline and its eval gate can reach the same models and no others.
