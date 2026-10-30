import io
import json
from collections.abc import Iterator
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError, NoCredentialsError
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

from triagelite.domain.errors import LLMProviderError, LLMRateLimitError
from triagelite.llm.bedrock import BedrockEmbeddingClient
from triagelite.llm.types import EmbeddingRequest
from triagelite.settings import Settings

REQUEST = EmbeddingRequest(
    model_id="amazon.titan-embed-text-v2:0", text="Login falla", dimensions=256, normalize=True
)


def body(payload: dict[str, object]) -> StreamingBody:
    raw = json.dumps(payload).encode("utf-8")
    return StreamingBody(io.BytesIO(raw), len(raw))


@pytest.fixture
def stubbed() -> Iterator[tuple[BedrockEmbeddingClient, Stubber]]:
    runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
    with Stubber(runtime) as stubber:
        yield BedrockEmbeddingClient(runtime), stubber
        stubber.assert_no_pending_responses()


def test_sends_titan_body_and_parses_vector(
    stubbed: tuple[BedrockEmbeddingClient, Stubber],
) -> None:
    client, stubber = stubbed
    stubber.add_response(
        "invoke_model",
        {
            "body": body({"embedding": [0.5] * 256, "inputTextTokenCount": 4, "extra": 1}),
            "contentType": "application/json",
        },
        {
            "modelId": "amazon.titan-embed-text-v2:0",
            "body": json.dumps({"inputText": "Login falla", "dimensions": 256, "normalize": True}),
            "contentType": "application/json",
            "accept": "application/json",
        },
    )

    response = client.embed(REQUEST)

    assert len(response.vector) == 256
    assert response.input_tokens == 4


def test_wrong_vector_size_is_a_permanent_error(
    stubbed: tuple[BedrockEmbeddingClient, Stubber],
) -> None:
    client, stubber = stubbed
    stubber.add_response(
        "invoke_model",
        {
            "body": body({"embedding": [0.1] * 10, "inputTextTokenCount": 1}),
            "contentType": "application/json",
        },
        {"modelId": ANY, "body": ANY, "contentType": ANY, "accept": ANY},
    )

    with pytest.raises(LLMProviderError, match="expected 256 dimensions") as raised:
        client.embed(REQUEST)

    assert raised.value.retryable is False


@pytest.mark.parametrize(
    ("code", "status", "expected", "retryable"),
    [
        ("ThrottlingException", 429, LLMRateLimitError, None),
        ("ServiceQuotaExceededException", 400, LLMRateLimitError, None),
        ("ServiceUnavailableException", 503, LLMProviderError, True),
        ("InternalServerException", 500, LLMProviderError, True),
        ("ModelNotReadyException", 429, LLMProviderError, True),
        ("ModelTimeoutException", 408, LLMProviderError, True),
        ("AccessDeniedException", 403, LLMProviderError, False),
        ("ValidationException", 400, LLMProviderError, False),
    ],
)
def test_service_errors_map_by_type(
    stubbed: tuple[BedrockEmbeddingClient, Stubber],
    code: str,
    status: int,
    expected: type[Exception],
    retryable: bool | None,
) -> None:
    client, stubber = stubbed
    stubber.add_client_error("invoke_model", service_error_code=code, http_status_code=status)

    with pytest.raises(expected) as raised:
        client.embed(REQUEST)

    if retryable is not None:
        assert isinstance(raised.value, LLMProviderError)
        assert raised.value.retryable is retryable


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (EndpointConnectionError(endpoint_url="https://bedrock"), True),
        (NoCredentialsError(), False),
    ],
)
def test_transport_errors_map_by_type(
    monkeypatch: pytest.MonkeyPatch, error: Exception, retryable: bool
) -> None:
    runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

    def fail(**_: object) -> None:
        raise error

    monkeypatch.setattr(runtime, "invoke_model", fail)

    with pytest.raises(LLMProviderError) as raised:
        BedrockEmbeddingClient(runtime).embed(REQUEST)

    assert raised.value.retryable is retryable


def test_from_settings_disables_botocore_retries() -> None:
    repo = Path(__file__).parents[2]
    client = BedrockEmbeddingClient.from_settings(
        Settings(config_dir=repo / "config", prompts_dir=repo / "prompts"), 30.0
    )

    options = vars(client._runtime.meta.config)
    assert options["retries"]["total_max_attempts"] == 1
    assert options["read_timeout"] == 30.0
