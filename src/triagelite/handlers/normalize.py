"""Stage 1: read the uploaded CSV, start the batch, and split its incidents into chunks."""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import PurePosixPath

from triagelite.domain.errors import InputValidationError
from triagelite.handlers.events import BatchEvent, NormalizeEvent, parse_event
from triagelite.handlers.runtime import batch_table, data_store, pipeline_config
from triagelite.handlers.work import NORMALIZED_FILE, chunk_key
from triagelite.logs import log_fields
from triagelite.pipeline.config import NormalizeConfig
from triagelite.pipeline.normalize import chunked, normalize
from triagelite.pipeline.stages import batch_id_for
from triagelite.storage.dynamo import BatchTable
from triagelite.storage.s3 import S3Store, work_key

LOGGER = logging.getLogger("triagelite.handlers.normalize")
STAGE = "normalize"


def run(
    event: NormalizeEvent,
    store: S3Store,
    table: BatchTable,
    config: NormalizeConfig,
    now: datetime,
) -> BatchEvent:
    """Write the normalized batch and one file per chunk.

    Raises:
        InputValidationError: the file is unusable; the batch is marked failed if it can be named.
    """
    content = store.read_text(event.source_key)
    batch_id = batch_id_for(PurePosixPath(event.source_key), content)
    table.start_batch(batch_id, event.source_key, now)
    try:
        normalized = normalize(content, config)
    except InputValidationError as error:
        table.fail_batch(batch_id, str(error), now)
        raise
    store.write_json(work_key(batch_id, NORMALIZED_FILE), normalized)
    chunk_keys = []
    for index, chunk in enumerate(chunked(normalized.incidents, config.chunk_size), start=1):
        key = chunk_key(batch_id, index)
        store.write_jsonl(key, chunk)
        chunk_keys.append(key)
    LOGGER.info(
        "normalized",
        extra=log_fields(
            batch_id=batch_id,
            stage=STAGE,
            incidents=len(normalized.incidents),
            row_errors=len(normalized.row_errors),
            chunks=len(chunk_keys),
        ),
    )
    return BatchEvent(batch_id=batch_id, chunk_keys=chunk_keys)


def handler(event: Mapping[str, object], _context: object) -> dict[str, object]:
    """Lambda entry point."""
    return run(
        parse_event(NormalizeEvent, event),
        data_store(),
        batch_table(),
        pipeline_config().normalize,
        datetime.now(UTC),
    ).model_dump(mode="json")
