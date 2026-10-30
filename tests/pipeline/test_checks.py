from triagelite.pipeline.checks import DUPLICATE_ANSWER, MISSING_ANSWER, check_answer_ids


def test_keeps_single_answers_and_explains_the_rest() -> None:
    answers = [("a", 1), ("b", 2), ("b", 3), ("zzz", 4)]

    check = check_answer_ids(answers, lambda answer: answer[0], {"a", "b", "c"})

    assert check.valid == {"a": ("a", 1)}
    assert check.problems == {"b": DUPLICATE_ANSWER, "c": MISSING_ANSWER}


def test_no_answers_means_every_id_is_missing() -> None:
    check = check_answer_ids(list[str](), str, {"x", "y"})

    assert check.valid == {}
    assert list(check.problems) == ["x", "y"]
