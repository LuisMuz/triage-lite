"""Model clients, kept apart from `runtime` so handlers without Bedrock skip the SDK import."""

from functools import lru_cache

from triagelite.handlers.runtime import lambda_settings, llm_config
from triagelite.llm.bedrock import BedrockEmbeddingClient, BedrockLLMClient


@lru_cache(maxsize=1)
def llm_client() -> BedrockLLMClient:
    """Claude, with SDK retries off."""
    models, _ = llm_config()
    return BedrockLLMClient.from_settings(lambda_settings(), models.client.timeout_seconds)


@lru_cache(maxsize=1)
def embedding_client() -> BedrockEmbeddingClient:
    """Titan, with SDK retries off."""
    models, _ = llm_config()
    return BedrockEmbeddingClient.from_settings(lambda_settings(), models.client.timeout_seconds)
