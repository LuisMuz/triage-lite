"""Stage 3: embed, judge and cluster, all in one invocation so vectors never leave memory."""

import logging
import time
from collections.abc import Mapping

from triagelite.domain.enums import Stage
from triagelite.handlers.bedrock import embedding_client, llm_client
from triagelite.handlers.events import BatchEvent, StageResult, parse_event
from triagelite.handlers.runtime import (
    CallLog,
    data_store,
    lambda_settings,
    llm_config,
    pipeline_config,
)
from triagelite.handlers.work import DEDUPE_CALLS, DEDUPE_FILE, NORMALIZED_FILE, calls_key
from triagelite.llm.client import EmbeddingClient, LLMClient
from triagelite.llm.config import ModelsConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.logs import log_fields
from triagelite.pipeline.backoff import Sleep
from triagelite.pipeline.config import PipelineConfig
from triagelite.pipeline.normalize import NormalizeResult
from triagelite.pipeline.stages import dedupe_batch
from triagelite.settings import load_stage_prompt
from triagelite.storage.s3 import S3Store, work_key

LOGGER = logging.getLogger("triagelite.handlers.dedupe")


def run(
    event: BatchEvent,
    store: S3Store,
    client: LLMClient,
    embedder: EmbeddingClient,
    prompt: PromptFile,
    models: ModelsConfig,
    prices: PriceTable,
    pipeline: PipelineConfig,
    calls: CallLog,
    sleep: Sleep = time.sleep,
) -> StageResult:
    """Write the batch's verdicts and clusters; the calls are kept even if it fails."""
    normalized = store.read_json(work_key(event.batch_id, NORMALIZED_FILE), NormalizeResult)
    try:
        result = dedupe_batch(
            StructuredLLM(client, models, prices, recorder=calls),
            prompt,
            embedder,
            normalized.incidents,
            models=models,
            prices=prices,
            config=pipeline.dedupe,
            retry=pipeline.chunk_retry,
            recorder=calls,
            batch_id=event.batch_id,
            sleep=sleep,
        )
    finally:
        store.write_jsonl(calls_key(event.batch_id, DEDUPE_CALLS), calls.records)
    key = work_key(event.batch_id, DEDUPE_FILE)
    store.write_json(key, result.outcome())
    LOGGER.info(
        "deduplicated",
        extra=log_fields(
            batch_id=event.batch_id, stage=Stage.DEDUPE_JUDGE, clusters=len(result.clusters)
        ),
    )
    return StageResult(batch_id=event.batch_id, keys=[key])


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    settings = lambda_settings()
    models, prices = llm_config()
    pipeline = pipeline_config()
    return run(
        parse_event(BatchEvent, event),
        data_store(),
        llm_client(),
        embedding_client(),
        load_stage_prompt(settings, Stage.DEDUPE_JUDGE, pipeline.prompts.dedupe_judge),
        models,
        prices,
        pipeline,
        CallLog(settings.metrics_namespace),
    ).model_dump(mode="json")
