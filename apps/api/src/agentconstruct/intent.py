from __future__ import annotations

import re
from typing import Protocol

from agentconstruct.domain import (
    EnvironmentName,
    IntentInterpretation,
    MaterialQuestion,
    WorkloadSpec,
)


class IntentProvider(Protocol):
    def interpret(self, prompt: str, source_repository: str | None) -> IntentInterpretation: ...


class DeterministicIntentProvider:
    """Local fixture parser. It is deliberately predictable and never silently fills critical gaps."""

    def interpret(self, prompt: str, source_repository: str | None) -> IntentInterpretation:
        lower = prompt.lower()
        average = self._number_before(lower, r"(\d+)\s*(?:requests?|rps)\s*(?:/|per)\s*(?:second|sec)")
        peak = self._number_after_word(lower, "peak")
        budget = self._number_before(lower, r"(?:under|below|budget)\s*\$?([\d,]+)")
        environments = [environment for environment in EnvironmentName if environment.value in lower]
        data_classification = "restricted" if any(word in lower for word in ("private", "customer data", "restricted")) else "unknown"
        workload_type = "rag_application" if "rag" in lower else "ai_api" if "api" in lower else "unknown"
        unknowns = []
        if not source_repository:
            unknowns.append("source_repository")
        if average is None:
            unknowns.append("average_rps")
        if peak is None:
            unknowns.append("peak_rps")
        if budget is None:
            unknowns.append("monthly_budget_usd")
        if not environments:
            unknowns.append("environments")
        provenance = {
            "cloud": "prompt" if "aws" in lower else "default: aws-only V1",
            "workload_type": "prompt" if workload_type != "unknown" else "unknown",
            "data_classification": "prompt" if data_classification != "unknown" else "unknown",
        }
        spec = WorkloadSpec(
            workload_type=workload_type,
            source_repository=source_repository,
            cloud="aws",
            data_classification=data_classification,
            average_rps=average,
            peak_rps=peak,
            monthly_budget_usd=budget,
            environments=environments,
            availability_target="99.9%" if "99.9" in lower else None,
            region_constraints=["us-east-1"] if "us-east-1" in lower else [],
            model_requirements={"runtime": "containerized"},
            integration_requirements=["slack"] if "slack" in lower else [],
            unknowns=unknowns,
            confidence=0.92 if not unknowns else 0.64,
            provenance=provenance,
        )
        return IntentInterpretation(
            spec=spec,
            questions=[MaterialQuestion(field=field, question=self._question_for(field), reason="AgentConstruct must not guess a value that changes architecture, security, or cost.") for field in unknowns],
        )

    @staticmethod
    def _question_for(field: str) -> str:
        return {
            "source_repository": "Which GitHub repository contains this workload?",
            "average_rps": "What average request rate should the system support?",
            "peak_rps": "What peak request rate should the system support?",
            "monthly_budget_usd": "What monthly infrastructure budget should the recommendation respect?",
            "environments": "Which environments are required, for example staging and production?",
        }[field]

    @staticmethod
    def _number_before(value: str, expression: str) -> int | None:
        match = re.search(expression, value)
        return int(match.group(1).replace(",", "")) if match else None

    @staticmethod
    def _number_after_word(value: str, word: str) -> int | None:
        match = re.search(rf"{word}[^\d]*(\d+)", value)
        return int(match.group(1)) if match else None
