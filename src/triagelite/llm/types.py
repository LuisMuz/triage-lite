"""Provider-neutral request/response types for one raw model call."""

from pydantic import JsonValue, NonNegativeInt, PositiveFloat, PositiveInt

from triagelite.domain.models import NonEmptyStr, StrictModel
from triagelite.llm.config import Effort, Thinking


class ToolSpec(StrictModel):
    """The single tool the model must call; `input_schema` is a Pydantic JSON schema."""

    name: NonEmptyStr
    description: NonEmptyStr
    input_schema: dict[str, JsonValue]


class ModelRequest(StrictModel):
    """Everything needed for one model call."""

    model_id: NonEmptyStr
    max_tokens: PositiveInt
    system: NonEmptyStr
    user: NonEmptyStr
    tool: ToolSpec
    thinking: Thinking | None = None
    effort: Effort | None = None
    timeout_seconds: PositiveFloat


class ToolCall(StrictModel):
    """One `tool_use` block from the response; `input` is still untrusted JSON."""

    name: str
    input: JsonValue


class ModelResponse(StrictModel):
    """The parts of a model response the pipeline uses."""

    stop_reason: str | None
    tool_calls: tuple[ToolCall, ...] = ()
    input_tokens: NonNegativeInt
    output_tokens: NonNegativeInt
