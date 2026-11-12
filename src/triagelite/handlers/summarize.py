"""Stage 4: compute the batch's numbers and write its report in each language."""

import logging
import time
from collections.abc import Mapping

from triagelite.domain.enums import Stage
from triagelite.handlers.bedrock import llm_client
from triagelite.handlers.events import BatchEvent, StageResult, parse_event
from triagelite.handlers.runtime import (
    CallLog,
    data_store,
    lambda_settings,
    llm_config,
    pipeline_config,
)
from triagelite.handlers.work import (
    DEDUPE_FILE,
    DRAFTS_FILE,
    FACTS_FILE,
    NORMALIZED_FILE,
    SUMMARIZE_CALLS,
    calls_key,
    load_results,
)
from triagelite.llm.client import LLMClient
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import log_fields
from triagelite.pipeline.aggregates import compute_facts
from triagelite.pipeline.backoff import Sleep
from triagelite.pipeline.config import PipelineConfig
from triagelite.pipeline.normalize import NormalizeResult
from triagelite.pipeline.stages import (
    REPORT_LANGUAGES,
    DedupeOutcome,
    render_draft,
    summarize_with_backoff,
)
from triagelite.settings import load_stage_prompt
from triagelite.storage.s3 import S3Store, report_key, work_key

LOGGER = logging.getLogger("triagelite.handlers.summarize")


def run(
    event: BatchEvent,
    store: S3Store,
    client: LLMClient,
    prompt: PromptFile,
    models: ModelsConfig,
    prices: PriceTable,
    pipeline: PipelineConfig,
    sleep: Sleep = time.sleep,
) -> StageResult:
    """Write the facts, drafts and reports; an unavailable model falls back to the template."""
    batch_id = event.batch_id
    normalized = store.read_json(work_key(batch_id, NORMALIZED_FILE), NormalizeResult)
    dedupe = store.read_json(work_key(batch_id, DEDUPE_FILE), DedupeOutcome)
    results = load_results(store, batch_id, event.chunk_keys, normalized.incidents)
    facts = compute_facts(
        normalized.incidents,
        results,
        dedupe.clusters,
        len(normalized.row_errors),
        pipeline.report,
    )
    store.write_json(work_key(batch_id, FACTS_FILE), facts)
    calls = CallLog()
    llm = StructuredLLM(client, models, prices, recorder=calls)
    try:
        drafts = [
            summarize_with_backoff(
                llm,
                prompt,
                facts,
                lang,
                pipeline.report,
                batch_id=batch_id,
                retry=pipeline.chunk_retry,
                sleep=sleep,
            )
            for lang in REPORT_LANGUAGES
        ]
    finally:
        store.write_jsonl(calls_key(batch_id, SUMMARIZE_CALLS), calls.records)
    store.write_jsonl(work_key(batch_id, DRAFTS_FILE), drafts)
    keys = []
    for draft in drafts:
        key = report_key(batch_id, draft.lang)
        store.write_text(
            key,
            render_draft(
                draft,
                facts,
                batch_id=batch_id,
                models=models,
                prompt=prompt,
                config=pipeline.report,
            ),
        )
        keys.append(key)
    LOGGER.info("reports written", extra=log_fields(batch_id=batch_id, stage=Stage.SUMMARIZE))
    return StageResult(batch_id=batch_id, keys=keys)


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    models, prices = llm_config()
    pipeline = pipeline_config()
    return run(
        parse_event(BatchEvent, event),
        data_store(),
        llm_client(),
        load_stage_prompt(lambda_settings(), Stage.SUMMARIZE, pipeline.prompts.summarize),
        models,
        prices,
        pipeline,
    ).model_dump(mode="json")
