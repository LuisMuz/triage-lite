"""Duplicate detection: candidate pairs from vectors, an LLM judge, then star clusters (TL-06)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape

import numpy as np

from triagelite.domain.errors import LLMOutputValidationError
from triagelite.domain.models import (
    CandidatePair,
    DuplicateCluster,
    Incident,
    JudgeOutput,
    PairJudgement,
    PairVerdict,
)
from triagelite.llm.prompts import PromptFile
from triagelite.llm.structured import StructuredLLM
from triagelite.pipeline.checks import AnswerCheck, check_answer_ids
from triagelite.pipeline.classify import render_incident
from triagelite.pipeline.config import DedupeConfig
from triagelite.pipeline.embed import EmbeddingMatrix, Matrix, similarity_matrix

PAIRS_VARIABLE = "pairs"
PAIR_ID_FORMAT = "p-{:04d}"
CLUSTER_ID_FORMAT = "cl-{:04d}"
SIMILARITY_DECIMALS = 4

_UNDATED = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class CandidateSet:
    """Pairs to judge, and how many more passed the filters but were cut by `max_pairs`."""

    pairs: list[CandidatePair]
    dropped: int


def report_order(incidents: Sequence[Incident]) -> list[str]:
    """Incident IDs, earliest `reported_at` first; undated last; ties keep input order."""

    def key(item: tuple[int, Incident]) -> tuple[bool, datetime, int]:
        index, incident = item
        reported = incident.reported_at
        if reported is None:
            return True, _UNDATED, index
        return False, reported if reported.tzinfo else reported.replace(tzinfo=UTC), index

    return [incident.incident_id for _, incident in sorted(enumerate(incidents), key=key)]


def top_k_pairs(similarity: Matrix, k: int) -> set[tuple[int, int]]:
    """Index pairs (i < j) where either side is among the other's k most similar items."""
    n = similarity.shape[0]
    masked = similarity.astype(np.float64)
    np.fill_diagonal(masked, -np.inf)
    keep: set[tuple[int, int]] = set()
    for i in range(n):
        for j in np.argsort(-masked[i])[: min(k, n - 1)]:
            keep.add((min(i, int(j)), max(i, int(j))))
    return keep


def candidate_pairs(
    matrix: EmbeddingMatrix, order: Sequence[str], config: DedupeConfig
) -> CandidateSet:
    """Pairs in either incident's top-k with similarity at or above the threshold.

    Above `max_pairs` the least similar pairs are dropped. In every pair `first_id` comes
    earlier in `order`, and pair IDs follow that order.
    """
    similarity = similarity_matrix(matrix.vectors)
    rank = {incident_id: position for position, incident_id in enumerate(order)}
    ids = matrix.incident_ids
    scored = [
        (float(similarity[i, j]), i, j)
        for i, j in top_k_pairs(similarity, config.top_k)
        if similarity[i, j] >= config.similarity_threshold
    ]
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    kept = scored[: config.max_pairs]
    oriented = [(sorted((ids[i], ids[j]), key=rank.__getitem__), score) for score, i, j in kept]
    oriented.sort(key=lambda item: (rank[item[0][0]], rank[item[0][1]]))
    pairs = [
        CandidatePair(
            pair_id=PAIR_ID_FORMAT.format(number),
            first_id=first,
            second_id=second,
            similarity=round(score, SIMILARITY_DECIMALS),
        )
        for number, ((first, second), score) in enumerate(oriented, start=1)
    ]
    return CandidateSet(pairs=pairs, dropped=len(scored) - len(kept))


def judge_chunk(
    llm: StructuredLLM,
    prompt: PromptFile,
    pairs: Sequence[CandidatePair],
    incidents: Mapping[str, Incident],
    *,
    batch_id: str,
) -> list[PairVerdict]:
    """Return one verdict per pair, in input order: judged, or unjudged with a reason.

    Pairs missing or answered twice are re-asked once, alone, with the reasons attached;
    whatever still fails stays unjudged and never merges. Availability errors propagate.
    """
    first = _ask(llm, prompt, pairs, incidents, batch_id=batch_id, feedback=())
    valid, problems = dict(first.valid), first.problems
    if problems:
        retry_pairs = [pair for pair in pairs if pair.pair_id in problems]
        feedback = [f"{pair_id}: {reason}" for pair_id, reason in problems.items()]
        second = _ask(llm, prompt, retry_pairs, incidents, batch_id=batch_id, feedback=feedback)
        valid |= second.valid
        problems = second.problems
    return [
        PairVerdict(pair=pair, judgement=valid[pair.pair_id])
        if pair.pair_id in valid
        else PairVerdict(pair=pair, reason=problems.get(pair.pair_id, "not judged"))
        for pair in pairs
    ]


def _ask(
    llm: StructuredLLM,
    prompt: PromptFile,
    pairs: Sequence[CandidatePair],
    incidents: Mapping[str, Incident],
    *,
    batch_id: str,
    feedback: Sequence[str],
) -> AnswerCheck[PairJudgement]:
    expected = {pair.pair_id for pair in pairs}
    variables = {PAIRS_VARIABLE: render_pairs(pairs, incidents)}
    try:
        result = llm.generate_structured(
            prompt, variables, JudgeOutput, batch_id=batch_id, feedback=feedback
        )
    except LLMOutputValidationError as error:
        reason = f"model output failed validation twice ({error})"
        return AnswerCheck(valid={}, problems=dict.fromkeys(sorted(expected), reason))
    return check_answer_ids(result.output.items, lambda item: item.pair_id, expected)


def unjudged(pairs: Sequence[CandidatePair], reason: str) -> list[PairVerdict]:
    """Verdicts for pairs the judge could not be reached for."""
    return [PairVerdict(pair=pair, reason=reason) for pair in pairs]


def render_pairs(pairs: Sequence[CandidatePair], incidents: Mapping[str, Incident]) -> str:
    """Each pair as a `<pair id="...">` holding its two `<incident>` blocks."""
    return "\n".join(
        "\n".join(
            [
                f'<pair id="{escape(pair.pair_id)}">',
                render_incident(incidents[pair.first_id]),
                render_incident(incidents[pair.second_id]),
                "</pair>",
            ]
        )
        for pair in pairs
    )


def star_clusters(
    order: Sequence[str], confirmed: Sequence[CandidatePair], max_size: int
) -> list[DuplicateCluster]:
    """Group incidents around canonicals without chaining.

    Incidents are visited in `order`. Each one joins the cluster whose canonical it was
    confirmed against directly (the most similar, if several) while that cluster has room;
    otherwise it becomes a canonical itself. Every incident ends up in exactly one cluster.
    """
    links = {frozenset((pair.first_id, pair.second_id)): pair.similarity for pair in confirmed}
    members: dict[str, list[str]] = {}
    for incident_id in order:
        options = [
            (links[frozenset((canonical, incident_id))], canonical)
            for canonical, group in members.items()
            if frozenset((canonical, incident_id)) in links and len(group) < max_size
        ]
        if options:
            _, canonical = max(options, key=lambda option: option[0])
            members[canonical].append(incident_id)
        else:
            members[incident_id] = [incident_id]
    return [
        DuplicateCluster(
            cluster_id=CLUSTER_ID_FORMAT.format(number), canonical_id=canonical, member_ids=group
        )
        for number, (canonical, group) in enumerate(members.items(), start=1)
    ]
