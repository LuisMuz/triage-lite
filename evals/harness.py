"""`python -m evals.harness --split tuning`: run the real classify pipeline over a frozen split."""

import argparse
import hashlib
import json
import re
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from pydantic import NonNegativeInt, PositiveInt, field_validator

import triagelite
from evals.dataset import (
    DATASETS_DIR,
    INCIDENTS_FILE,
    LABELS_FILE,
    MANIFEST_FILE,
    EvalLabel,
    Manifest,
    Split,
    read_jsonl,
)
from evals.metrics import ClassifyMetrics, ItemPrediction, compute_metrics
from evals.report import render_markdown
from evals.validate import validate
from triagelite.domain.enums import Stage, TriageStatus
from triagelite.domain.models import (
    Incident,
    IncidentClassification,
    LLMCallRecord,
    NonEmptyStr,
    RawIncident,
    StrictModel,
)
from triagelite.domain.taxonomy import Taxonomy
from triagelite.llm.bedrock import BedrockLLMClient
from triagelite.llm.client import LLMClient
from triagelite.llm.config import ModelApi, StageModelConfig
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.backoff import AvailabilityError, Sleep, with_backoff
from triagelite.pipeline.classify import classify_chunk, render_incidents
from triagelite.pipeline.normalize import chunked, normalize_rows
from triagelite.settings import (
    Settings,
    get_settings,
    load_llm_config,
    load_pipeline_config,
    load_stage_prompt,
    load_taxonomy,
)

RESULTS_DIR = Path(__file__).parent / "results"
CACHE_DIR = Path(__file__).parent / "cache"
PACKAGE_DIR = Path(triagelite.__file__).parent
EXIT_UNAVAILABLE = 3
PROMPT_ID_PATTERN = re.compile(r"^(?P<stage>[a-z_]+)/v(?P<version>\d+)$")
MODEL_SLUG_PATTERN = re.compile(r"claude-[a-z]+-\d+(?:-\d+)?")


class EvalError(Exception):
    """The eval can't run as requested; the message says why."""


class EvalUnavailableError(Exception):
    """Bedrock stayed unavailable for a chunk after backoff; rerun later, the cache resumes."""


class ChunkOutcome(StrictModel):
    """Cached result of classifying one chunk: per-incident outcomes and every call made."""

    results: list[IncidentClassification]
    records: list[LLMCallRecord]


class EvalResult(StrictModel):
    """One harness run: what was evaluated, with what, and every prediction and metric."""

    created_at: NonEmptyStr
    dataset: NonEmptyStr
    dataset_labels_sha256: NonEmptyStr
    split: Split
    prompt: NonEmptyStr
    model_id: NonEmptyStr
    model: StageModelConfig
    repeat: PositiveInt
    chunk_size: PositiveInt
    fresh_calls: NonNegativeInt
    cached_chunks: NonNegativeInt
    metrics: ClassifyMetrics
    labels: list[EvalLabel]
    predictions: list[ItemPrediction]

    @field_validator("model", mode="before")
    @classmethod
    def _results_before_api_used_messages(cls, value: object) -> object:
        """Results written before `api` existed were all produced with the Messages API."""
        if isinstance(value, dict) and "api" not in value:
            return {**value, "api": "messages"}
        return value


def parse_prompt_id(prompt_id: str) -> tuple[Stage, int]:
    """`classify/v1` to (Stage.CLASSIFY, 1)."""
    match = PROMPT_ID_PATTERN.match(prompt_id)
    if not match:
        raise EvalError(f"prompt must look like 'classify/v1', got {prompt_id!r}")
    return Stage(match["stage"]), int(match["version"])


def model_slug(model_id: str) -> str:
    """Short model name for file names, e.g. `claude-haiku-4-5`."""
    match = MODEL_SLUG_PATTERN.search(model_id)
    return match.group() if match else re.sub(r"[^a-z0-9]+", "-", model_id.lower()).strip("-")


def code_fingerprint(package_dir: Path) -> str:
    """Hash of every Python file's path and contents, so a code change misses the cache."""
    digest = hashlib.sha256()
    for path in sorted(package_dir.rglob("*.py")):
        digest.update(path.relative_to(package_dir).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def cache_key(
    prompt: PromptFile,
    model: StageModelConfig,
    taxonomy: Taxonomy,
    chunk_text: str,
    repeat: int,
    code: str,
) -> str:
    """Identical prompt, model settings, taxonomy, input and pipeline code give the same key.

    The cache holds validated outcomes, so code that parses or checks the answer is part of it.
    """
    payload = {
        "prompt": prompt.model_dump(mode="json"),
        "model": model.model_dump(mode="json"),
        "taxonomy": taxonomy.model_dump(mode="json"),
        "input": chunk_text,
        "repeat": repeat,
        "code": code,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def load_split(
    dataset_dir: Path, split: Split, taxonomy: Taxonomy
) -> tuple[list[RawIncident], dict[str, EvalLabel], Manifest]:
    """Verify the frozen dataset, then return one split's incidents and gold labels."""
    failures = validate(dataset_dir, taxonomy)
    if failures:
        raise EvalError("dataset failed validation:\n" + "\n".join(failures))
    manifest = Manifest.model_validate_json((dataset_dir / MANIFEST_FILE).read_text("utf-8"))
    labels = {
        label.external_id: label
        for label in read_jsonl(dataset_dir / LABELS_FILE, EvalLabel)
        if label.split is split
    }
    incidents = sorted(
        (
            i
            for i in read_jsonl(dataset_dir / INCIDENTS_FILE, RawIncident)
            if i.external_id in labels
        ),
        key=lambda incident: incident.external_id,
    )
    return incidents, labels, manifest


def run_eval(
    *,
    dataset: str,
    split: Split,
    prompt_id: str,
    repeat: int,
    settings: Settings,
    client: LLMClient,
    chunk_size: int | None = None,
    model_id: str | None = None,
    api: ModelApi | None = None,
    datasets_dir: Path = DATASETS_DIR,
    cache_dir: Path = CACHE_DIR,
    code_dir: Path = PACKAGE_DIR,
    sleep: Sleep = time.sleep,
) -> EvalResult:
    """Normalize and classify every item of `split`, `repeat` times, then compute metrics.

    `chunk_size` overrides the configured number of incidents per call; `model_id` and `api`
    swap the stage's model (thinking and effort are cleared, max_tokens is kept). A chunk still
    unavailable after backoff raises `EvalUnavailableError` instead of scoring as needs_manual,
    so throttling never reads as a quality drop and is never cached.
    """
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    stage, version = parse_prompt_id(prompt_id)
    prompt = load_stage_prompt(settings, stage, version)
    model = models.for_stage(stage)
    if model_id:
        model = StageModelConfig(
            model_id=model_id, api=api or model.api, max_tokens=model.max_tokens
        )
        models = models.model_copy(update={"stages": {**models.stages, stage: model}})
    raw, labels, manifest = load_split(datasets_dir / dataset, split, taxonomy)
    incidents = normalize_rows(raw, pipeline.normalize).incidents
    size = chunk_size or pipeline.normalize.chunk_size
    code = code_fingerprint(code_dir)

    predictions: list[ItemPrediction] = []
    records: list[LLMCallRecord] = []
    fresh_calls = cached_chunks = 0
    for run in range(repeat):
        for chunk in chunked(incidents, size):
            key = cache_key(prompt, model, taxonomy, render_incidents(chunk), run, code)
            path = cache_dir / f"{key}.json"
            if path.exists():
                outcome = ChunkOutcome.model_validate_json(path.read_text("utf-8"))
                cached_chunks += 1
            else:
                chunk_records: list[LLMCallRecord] = []
                llm = StructuredLLM(client, models, prices, recorder=chunk_records.append)
                batch_id = f"eval-{dataset}-{split}-r{run}"
                results = with_backoff(
                    partial(classify_chunk, llm, prompt, taxonomy, chunk, batch_id=batch_id),
                    retry=pipeline.chunk_retry,
                    sleep=sleep,
                    exhausted=_unavailable,
                )
                outcome = ChunkOutcome(results=results, records=chunk_records)
                fresh_calls += len(chunk_records)
                cache_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(outcome.model_dump_json(), encoding="utf-8")
            records += outcome.records
            predictions += _to_predictions(chunk, outcome.results, run)

    return EvalResult(
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        dataset=dataset,
        dataset_labels_sha256=manifest.sha256[LABELS_FILE],
        split=split,
        prompt=prompt.id,
        model_id=model.model_id,
        model=model,
        repeat=repeat,
        chunk_size=size,
        fresh_calls=fresh_calls,
        cached_chunks=cached_chunks,
        metrics=compute_metrics(labels, predictions, records),
        labels=[labels[external_id] for external_id in sorted(labels)],
        predictions=predictions,
    )


def _unavailable(attempts: int, error: AvailabilityError) -> list[IncidentClassification]:
    raise EvalUnavailableError(
        f"a chunk was still unavailable after {attempts} attempts ({type(error).__name__}: "
        f"{error}); completed chunks are cached, so rerunning resumes"
    )


def _to_predictions(
    chunk: Sequence[Incident], results: Sequence[IncidentClassification], run: int
) -> list[ItemPrediction]:
    by_id = {result.incident_id: result for result in results}
    predictions = []
    for incident in chunk:
        result = by_id[incident.incident_id]
        labels = result.classification
        predictions.append(
            ItemPrediction(
                external_id=incident.external_id,
                repeat=run,
                title=incident.title,
                detected_lang=incident.lang,
                severity=labels.severity if labels else None,
                category=labels.category if labels else None,
                component=labels.component if labels else None,
                confidence=labels.confidence if labels else None,
                rationale=labels.rationale if labels else None,
                reason=result.reason if result.status is TriageStatus.NEEDS_MANUAL else None,
            )
        )
    return predictions


def result_stem(result: EvalResult) -> str:
    """`<prompt>-<model>-<split>-c<chunk size>[-x<repeat>]`, e.g. `classify-v2-…-tuning-c10-x3`."""
    stem = "-".join(
        [
            result.prompt.replace("/", "-"),
            model_slug(result.model_id),
            result.split.value,
            f"c{result.chunk_size}",
        ]
    )
    return stem + (f"-x{result.repeat}" if result.repeat > 1 else "")


def write_result(result: EvalResult, results_dir: Path = RESULTS_DIR) -> tuple[Path, Path]:
    """Write `<date>-<stem>.json` and a matching Markdown report."""
    stem = f"{result.created_at[:10]}-{result_stem(result)}"
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = results_dir / f"{stem}.json", results_dir / f"{stem}.md"
    json_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        render_markdown(
            title=f"{result.prompt} · {result.model_id} · {result.dataset}/{result.split}",
            subtitle=(
                f"Run {result.created_at} · repeat {result.repeat} · "
                f"{result.chunk_size} incidents per call · "
                f"{result.metrics.items} items · {result.metrics.llm_calls} calls "
                f"({result.fresh_calls} fresh, {result.cached_chunks} cached chunks)"
            ),
            prompt=result.prompt,
            model_id=result.model_id,
            split=result.split.value,
            metrics=result.metrics,
            predictions=result.predictions,
            labels={label.external_id: label for label in result.labels},
        ),
        encoding="utf-8",
    )
    return json_path, md_path


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: `python -m evals.harness --split tuning --prompt classify/v1`."""
    parser = argparse.ArgumentParser(prog="python -m evals.harness", description=__doc__)
    parser.add_argument("--dataset", default="seed-v1")
    parser.add_argument("--split", type=Split, choices=list(Split), default=Split.TUNING)
    parser.add_argument(
        "--prompt", default=None, help="stage/version, e.g. classify/v1 (default: config)"
    )
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument(
        "--chunk-size", type=int, default=None, help="incidents per call (default: config)"
    )
    parser.add_argument("--model", default=None, help="Bedrock model id (default: config)")
    parser.add_argument("--api", choices=["messages", "converse"], default=None)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--confirm-holdout",
        action="store_true",
        help="required for --split holdout: the holdout is run once, for the reported number",
    )
    args = parser.parse_args(argv)
    if args.split is Split.HOLDOUT and not args.confirm_holdout:
        sys.stderr.write("refusing to run holdout without --confirm-holdout\n")
        return 1
    if args.repeat < 1:
        sys.stderr.write("--repeat must be at least 1\n")
        return 1
    if args.chunk_size is not None and args.chunk_size < 1:
        sys.stderr.write("--chunk-size must be at least 1\n")
        return 1
    settings = get_settings()
    models, _ = load_llm_config(settings)
    prompt_id = (
        args.prompt or f"{Stage.CLASSIFY}/v{load_pipeline_config(settings).prompts.classify}"
    )
    try:
        result = run_eval(
            dataset=args.dataset,
            split=args.split,
            prompt_id=prompt_id,
            repeat=args.repeat,
            settings=settings,
            client=BedrockLLMClient.from_settings(settings, models.client.timeout_seconds),
            chunk_size=args.chunk_size,
            model_id=args.model,
            api=args.api,
        )
    except EvalError as error:
        sys.stderr.write(f"eval failed: {error}\n")
        return 1
    except EvalUnavailableError as error:
        sys.stderr.write(f"eval unavailable: {error}\n")
        return EXIT_UNAVAILABLE
    json_path, md_path = write_result(result, args.results_dir)
    metrics = result.metrics
    f1 = metrics.severity_macro_f1
    sys.stdout.write(
        f"{result.prompt} · {model_slug(result.model_id)} · {result.split} · "
        f"macro-F1 {f1.value:.3f} [{f1.low:.3f}-{f1.high:.3f}] · "
        f"${metrics.cost_per_100_incidents_usd:.3f}/100 · "
        f"{result.fresh_calls} fresh calls, {result.cached_chunks} cached chunks\n"
        f"wrote {json_path} and {md_path}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
