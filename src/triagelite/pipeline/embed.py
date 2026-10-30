"""Incidents to vectors (one embedding call each) and their pairwise cosine similarity."""

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

import numpy as np
import numpy.typing as npt

from triagelite.domain.enums import CallStatus, Stage
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError, TriageError
from triagelite.domain.models import Incident, LLMCallRecord
from triagelite.llm.client import CallRecorder, EmbeddingClient
from triagelite.llm.config import EmbeddingConfig
from triagelite.llm.pricing import PriceTable
from triagelite.llm.types import EmbeddingRequest, EmbeddingResponse

type Matrix = npt.NDArray[np.float32]


@dataclass(frozen=True)
class EmbeddingMatrix:
    """One row per incident, in `incident_ids` order, plus what produced the vectors."""

    model_id: str
    dimensions: int
    incident_ids: tuple[str, ...]
    vectors: Matrix


def embedding_text(incident: Incident, max_description_chars: int) -> str:
    """Title plus the start of the description, so pasted stack traces don't dominate."""
    return f"{incident.title}\n{incident.description[:max_description_chars]}"


def embed_incidents(
    client: EmbeddingClient,
    incidents: Sequence[Incident],
    config: EmbeddingConfig,
    prices: PriceTable,
    recorder: CallRecorder,
    *,
    batch_id: str | None = None,
) -> EmbeddingMatrix:
    """Embed every incident, recording one `LLMCallRecord` per call (stage `embed`).

    Availability errors propagate after their record is written, like the classify stage.
    """
    rows = [
        _embed_one(client, incident, config, prices, recorder, batch_id).vector
        for incident in incidents
    ]
    vectors = np.array(rows, dtype=np.float32).reshape(len(rows), config.dimensions)
    return EmbeddingMatrix(
        model_id=config.model_id,
        dimensions=config.dimensions,
        incident_ids=tuple(incident.incident_id for incident in incidents),
        vectors=vectors,
    )


def _embed_one(
    client: EmbeddingClient,
    incident: Incident,
    config: EmbeddingConfig,
    prices: PriceTable,
    recorder: CallRecorder,
    batch_id: str | None,
) -> EmbeddingResponse:
    request = EmbeddingRequest(
        model_id=config.model_id,
        text=embedding_text(incident, config.max_description_chars),
        dimensions=config.dimensions,
        normalize=config.normalize,
    )
    started = perf_counter()
    try:
        response = client.embed(request)
    except (LLMRateLimitError, LLMProviderError) as error:
        recorder(_record(config, prices, started, batch_id, None, error))
        raise
    recorder(_record(config, prices, started, batch_id, response, None))
    return response


def _record(
    config: EmbeddingConfig,
    prices: PriceTable,
    started: float,
    batch_id: str | None,
    response: EmbeddingResponse | None,
    error: TriageError | None,
) -> LLMCallRecord:
    tokens = response.input_tokens if response else 0
    if error is None:
        status = CallStatus.OK
    elif isinstance(error, LLMRateLimitError):
        status = CallStatus.RATE_LIMITED
    else:
        status = CallStatus.PROVIDER_ERROR
    return LLMCallRecord(
        call_id=uuid4().hex,
        stage=Stage.EMBED,
        model_id=config.model_id,
        prompt_version=None,
        input_tokens=tokens,
        output_tokens=0,
        cost_usd=prices.cost_usd(config.model_id, tokens, 0),
        latency_ms=round((perf_counter() - started) * 1000),
        stop_reason=None,
        attempt=1,
        status=status,
        error_type=type(error).__name__ if error else None,
        batch_id=batch_id,
    )


def similarity_matrix(vectors: Matrix) -> Matrix:
    """Cosine similarity of every pair; rows are re-normalized so this holds for any input."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    unit = np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)
    similarity: Matrix = (unit @ unit.T).astype(np.float32)
    return similarity
