from enum import StrEnum


class Severity(StrEnum):
    """How bad an incident is; definitions live in config/taxonomy.toml."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(StrEnum):
    """What kind of defect an incident is; definitions live in config/taxonomy.toml."""

    FUNCTIONAL = "functional"
    UI = "ui"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATA = "data"
    CRASH = "crash"


class Stage(StrEnum):
    """Pipeline stages that call a model (LLM or embeddings)."""

    CLASSIFY = "classify"
    EMBED = "embed"
    DEDUPE_JUDGE = "dedupe_judge"
    SUMMARIZE = "summarize"


class CallStatus(StrEnum):
    """Outcome of one model call attempt."""

    OK = "ok"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    PROVIDER_ERROR = "provider_error"
