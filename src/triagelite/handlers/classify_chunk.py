"""Stage 2, once per chunk: availability errors propagate so Step Functions can back off."""

import logging
from collections.abc import Mapping

from triagelite.domain.enums import Stage, TriageStatus
from triagelite.domain.models import Incident
from triagelite.domain.taxonomy import Taxonomy
from triagelite.handlers.bedrock import llm_client
from triagelite.handlers.events import ChunkEvent, StageResult, parse_event
from triagelite.handlers.runtime import (
    CallLog,
    data_store,
    lambda_settings,
    llm_config,
    pipeline_config,
)
from triagelite.handlers.work import calls_key, chunk_calls_name, classified_key
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import log_fields
from triagelite.pipeline.classify import classify_chunk
from triagelite.settings import load_stage_prompt, load_taxonomy
from triagelite.storage.s3 import S3Store

LOGGER = logging.getLogger("triagelite.handlers.classify_chunk")


def run(
    event: ChunkEvent,
    store: S3Store,
    llm: StructuredLLM,
    prompt: PromptFile,
    taxonomy: Taxonomy,
    calls: CallLog,
) -> StageResult:
    """Classify one stored chunk and write its results; the calls are kept even if it fails."""
    incidents = store.read_jsonl(event.chunk_key, Incident)
    result_key = classified_key(event.batch_id, event.chunk_key)
    try:
        results = classify_chunk(llm, prompt, taxonomy, incidents, batch_id=event.batch_id)
        store.write_jsonl(result_key, results)
    finally:
        store.write_jsonl(
            calls_key(event.batch_id, chunk_calls_name(event.chunk_key)), calls.records
        )
    LOGGER.info(
        "chunk classified",
        extra=log_fields(
            batch_id=event.batch_id,
            stage=Stage.CLASSIFY,
            chunk_key=event.chunk_key,
            needs_manual=sum(result.status is TriageStatus.NEEDS_MANUAL for result in results),
        ),
    )
    return StageResult(batch_id=event.batch_id, keys=[result_key])


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    settings = lambda_settings()
    models, prices = llm_config()
    calls = CallLog(settings.metrics_namespace)
    return run(
        parse_event(ChunkEvent, event),
        data_store(),
        StructuredLLM(llm_client(), models, prices, recorder=calls),
        load_stage_prompt(settings, Stage.CLASSIFY, pipeline_config().prompts.classify),
        load_taxonomy(settings),
        calls,
    ).model_dump(mode="json")
