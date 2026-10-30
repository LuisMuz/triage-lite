"""ID-set checks for stages that ask the model for exactly one answer per item."""

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass

DUPLICATE_ANSWER = "answered more than once; answer exactly once"
MISSING_ANSWER = "missing from your answer"


@dataclass(frozen=True)
class AnswerCheck[T]:
    """Answers that passed, and a reason for every expected ID that didn't."""

    valid: dict[str, T]
    problems: dict[str, str]


def check_answer_ids[T](
    items: Sequence[T], key: Callable[[T], str], expected_ids: set[str]
) -> AnswerCheck[T]:
    """Keep answers whose ID was asked for and answered exactly once; ignore unexpected IDs."""
    counts = Counter(key(item) for item in items)
    valid: dict[str, T] = {}
    problems: dict[str, str] = {}
    for item in items:
        item_id = key(item)
        if item_id not in expected_ids:
            continue
        if counts[item_id] > 1:
            problems[item_id] = DUPLICATE_ANSWER
        else:
            valid[item_id] = item
    for missing in sorted(expected_ids - counts.keys()):
        problems[missing] = MISSING_ANSWER
    return AnswerCheck(valid=valid, problems=problems)
