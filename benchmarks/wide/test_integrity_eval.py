from pathlib import Path

import integrity_eval


HERE = Path(__file__).parent


def test_eval09_mutations_cannot_fool_scorer():
    golden = HERE / "eval_forms" / "eval_09" / "golden.xlsx"
    result = integrity_eval.integrity_test(golden)
    assert result["passed"], result["checks"]


def test_strict_metrics_are_not_headline_for_consensus_golden():
    golden = HERE / "eval_forms" / "eval_09" / "golden.xlsx"
    result = integrity_eval.score(golden, golden)
    assert result["exact_cell"]["f1"] == 1.0
    assert result["strict_metrics_are_headline"] is False
