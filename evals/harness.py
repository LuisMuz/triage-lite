"""`python -m evals.harness --split tuning`: run the real classify pipeline over a frozen split."""

import argparse
import hashlib
import json
import re
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import NonNegativeInt, PositiveInt

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
from triagelite.cli import Sleep, classify_with_backoff
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
from triagelite.llm.config import StageModelConfig
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.classify import render_incidents
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
PROMPT_ID_PATTERN = re.compile(r"^(?P<stage>[a-z_]+)/v(?P<version>\d+)$")
MODEL_SLUG_PATTERN = re.compile(r"claude-[a-z]+-\d+(?:-\d+)?")


class EvalError(Exception):
    """The eval can't run as requested; the message says why."""


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
    fresh_calls: NonNegativeInt
    cached_chunks: NonNegativeInt
    metrics: ClassifyMetrics
    labels: list[EvalLabel]
    predictions: list[ItemPrediction]


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


def cache_key(
    prompt: PromptFile, model: StageModelConfig, taxonomy: Taxonomy, chunk_text: str, repeat: int
) -> str:
    """Identical prompt, model settings, taxonomy and input give the same key."""
    payload = {
        "prompt": prompt.model_dump(mode="json"),
        "model": model.model_dump(mode="json"),
        "taxonomy": taxonomy.model_dump(mode="json"),
        "input": chunk_text,
        "repeat": repeat,
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
    datasets_dir: Path = DATASETS_DIR,
    cache_dir: Path = CACHE_DIR,
    sleep: Sleep = time.sleep,
) -> EvalResult:
    """Normalize and classify every item of `split`, `repeat` times, then compute metrics."""
    taxonomy = load_taxonomy(settings)
    models, prices = load_llm_config(settings)
    pipeline = load_pipeline_config(settings)
    stage, version = parse_prompt_id(prompt_id)
    prompt = load_stage_prompt(settings, stage, version)
    model = models.for_stage(stage)
    raw, labels, manifest = load_split(datasets_dir / dataset, split, taxonomy)
    incidents = normalize_rows(raw, pipeline.normalize).incidents

    predictions: list[ItemPrediction] = []
    records: list[LLMCallRecord] = []
    fresh_calls = cached_chunks = 0
    for run in range(repeat):
        for chunk in chunked(incidents, pipeline.normalize.chunk_size):
            key = cache_key(prompt, model, taxonomy, render_incidents(chunk), run)
            path = cache_dir / f"{key}.json"
            if path.exists():
                outcome = ChunkOutcome.model_validate_json(path.read_text("utf-8"))
                cached_chunks += 1
            else:
                chunk_records: list[LLMCallRecord] = []
                llm = StructuredLLM(client, models, prices, recorder=chunk_records.append)
                results = classify_with_backoff(
                    llm,
                    prompt,
                    taxonomy,
                    chunk,
                    batch_id=f"eval-{dataset}-{split}-r{run}",
                    retry=pipeline.local_retry,
                    sleep=sleep,
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
        fresh_calls=fresh_calls,
        cached_chunks=cached_chunks,
        metrics=compute_metrics(labels, predictions, records),
        labels=[labels[external_id] for external_id in sorted(labels)],
        predictions=predictions,
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


def write_result(result: EvalResult, results_dir: Path = RESULTS_DIR) -> tuple[Path, Path]:
    """Write `<date>-<prompt>-<model>-<split>.json` and a matching Markdown report."""
    date = result.created_at[:10]
    stem = "-".join(
        [date, result.prompt.replace("/", "-"), model_slug(result.model_id), result.split.value]
    )
    if result.repeat > 1:
        stem += f"-x{result.repeat}"
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = results_dir / f"{stem}.json", results_dir / f"{stem}.md"
    json_path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        render_markdown(
            title=f"{result.prompt} · {result.model_id} · {result.dataset}/{result.split}",
            subtitle=(
                f"Run {result.created_at} · repeat {result.repeat} · "
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
    parser.add_argument("--prompt", default="classify/v1", help="stage/version, e.g. classify/v1")
    parser.add_argument("--repeat", type=int, default=1)
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
    settings = get_settings()
    try:
        result = run_eval(
            dataset=args.dataset,
            split=args.split,
            prompt_id=args.prompt,
            repeat=args.repeat,
            settings=settings,
            client=BedrockLLMClient.from_settings(settings),
        )
    except EvalError as error:
        sys.stderr.write(f"eval failed: {error}\n")
        return 1
    json_path, md_path = write_result(result)
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
