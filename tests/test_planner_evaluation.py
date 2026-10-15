import json
from pathlib import Path

from agentconstruct.evaluation import run_default_benchmark


def test_default_planner_benchmark_passes():
    results = run_default_benchmark()
    assert all(result.passed for result in results), results


def test_benchmark_includes_non_eks_and_gpu_cases():
    results = {result.name: result for result in run_default_benchmark()}
    assert "eks" not in results["tiny-stateless-api"].selected_profile.lower()
    assert results["gpu-multiservice-inference"].selected_profile == "aws-eks-governed"


def test_benchmark_corpus_records_expected_outcomes_and_unknown_case():
    corpus = json.loads(Path("tests/fixtures/planner_benchmark.json").read_text())
    assert {case["name"] for case in corpus} >= {"tiny-stateless-api", "gpu-multiservice-inference", "unsupported-unknown-runtime"}
    assert corpus[-1]["expected_behavior"] == "needs-clarification"
