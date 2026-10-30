import numpy as np
import pytest

from tests.pipeline.conftest import make_incident
from triagelite.domain.enums import CallStatus, Stage
from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.domain.models import LLMCallRecord
from triagelite.llm.config import EmbeddingConfig
from triagelite.llm.fake import FakeEmbeddingClient
from triagelite.llm.pricing import PriceTable
from triagelite.llm.types import EmbeddingRequest
from triagelite.pipeline.embed import embed_incidents, embedding_text, similarity_matrix

CONFIG = EmbeddingConfig(model_id="titan", dimensions=256, normalize=True, max_description_chars=10)
PRICES = PriceTable.model_validate(
    {"models": {"titan": {"input_per_mtok": 0.02, "output_per_mtok": 0.0}}}
)


def test_embedding_text_is_title_plus_truncated_description() -> None:
    incident = make_incident(1).model_copy(update={"description": "0123456789-tail"})

    assert embedding_text(incident, 10) == "Checkout fails 1\n0123456789"


def test_embeds_every_incident_in_order_and_records_cost() -> None:
    records: list[LLMCallRecord] = []
    client = FakeEmbeddingClient()

    matrix = embed_incidents(
        client, [make_incident(1), make_incident(2)], CONFIG, PRICES, records.append, batch_id="b"
    )

    assert matrix.vectors.shape == (2, 256)
    assert matrix.vectors.dtype == np.float32
    assert matrix.incident_ids == ("inc-0001", "inc-0002")
    assert (matrix.model_id, matrix.dimensions) == ("titan", 256)
    assert [request.dimensions for request in client.requests] == [256, 256]
    assert all(r.stage is Stage.EMBED and r.status is CallStatus.OK for r in records)
    assert all(r.batch_id == "b" and r.output_tokens == 0 for r in records)
    assert records[0].cost_usd == pytest.approx(records[0].input_tokens * 0.02 / 1_000_000)


def test_empty_batch_gives_an_empty_matrix() -> None:
    matrix = embed_incidents(FakeEmbeddingClient(), [], CONFIG, PRICES, lambda _: None)

    assert matrix.vectors.shape == (0, 256)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (LLMRateLimitError("429"), CallStatus.RATE_LIMITED),
        (LLMProviderError("403", retryable=False), CallStatus.PROVIDER_ERROR),
    ],
)
def test_failures_are_recorded_then_raised(
    error: LLMRateLimitError | LLMProviderError, status: CallStatus
) -> None:
    records: list[LLMCallRecord] = []

    with pytest.raises(type(error)):
        embed_incidents(
            FakeEmbeddingClient(failures=[error]),
            [make_incident(1)],
            CONFIG,
            PRICES,
            records.append,
        )

    assert [(r.status, r.error_type, r.cost_usd) for r in records] == [
        (status, type(error).__name__, 0.0)
    ]


def test_similarity_is_cosine_even_for_unnormalized_rows() -> None:
    vectors = np.array([[3.0, 0.0], [1.0, 1.0], [0.0, 2.0], [0.0, 0.0]], dtype=np.float32)

    similarity = similarity_matrix(vectors)

    assert similarity[0, 0] == pytest.approx(1.0)
    assert similarity[0, 1] == pytest.approx(np.sqrt(0.5), rel=1e-5)
    assert similarity[0, 2] == pytest.approx(0.0)
    assert similarity[3, 0] == 0.0
    assert np.allclose(similarity, similarity.T)


def test_fake_vectors_are_deterministic_unit_vectors() -> None:
    request = EmbeddingRequest(model_id="titan", text="same text", dimensions=256, normalize=True)

    first, second = FakeEmbeddingClient().embed(request), FakeEmbeddingClient().embed(request)

    assert first.vector == second.vector
    assert np.linalg.norm(first.vector) == pytest.approx(1.0)
