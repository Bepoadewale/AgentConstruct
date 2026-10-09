"""Thin operator/developer CLI. It forwards a caller's token to the governed API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from agentconstruct.client import ProductApiClient


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AgentConstruct governed API client")
    parser.add_argument(
        "--api-url", default=os.getenv("AGENTCONSTRUCT_API_URL", "http://127.0.0.1:8080")
    )
    parser.add_argument("--token", default=os.getenv("AGENTCONSTRUCT_TOKEN"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    intent = subparsers.add_parser("analyze-workload")
    intent.add_argument("--project-id", required=True)
    intent.add_argument("--prompt", required=True)
    intent.add_argument("--idempotency-key", required=True)
    intent.add_argument("--repository")
    intent.add_argument("--cloud-connection-id")

    plan = subparsers.add_parser("plan-infrastructure")
    plan.add_argument("--intent-id", required=True)

    get_plan = subparsers.add_parser("get-plan")
    get_plan.add_argument("--plan-id", required=True)

    compare = subparsers.add_parser("compare-architectures")
    compare.add_argument("--plan-id", required=True)

    execute = subparsers.add_parser("execute-approved-plan")
    execute.add_argument("--plan-id", required=True)

    environment = subparsers.add_parser("get-environment-status")
    environment.add_argument("--environment-id", required=True)

    audit = subparsers.add_parser("get-audit-events")
    audit.add_argument("--environment-id")

    destroy = subparsers.add_parser("destroy-environment")
    destroy.add_argument("--environment-id", required=True)
    return parser


def run(
    args: argparse.Namespace, client: ProductApiClient
) -> dict[str, Any] | list[dict[str, Any]]:
    if args.command == "analyze-workload":
        return client.request(
            "POST",
            "/api/v1/intents",
            {
                "project_id": args.project_id,
                "prompt": args.prompt,
                "source_repository": args.repository,
                "cloud_connection_id": args.cloud_connection_id,
                "idempotency_key": args.idempotency_key,
            },
        )
    if args.command == "plan-infrastructure":
        return client.request("POST", f"/api/v1/intents/{args.intent_id}/plans")
    if args.command == "get-plan":
        return client.request("GET", f"/api/v1/deployment-plans/{args.plan_id}")
    if args.command == "compare-architectures":
        plan = client.request("GET", f"/api/v1/deployment-plans/{args.plan_id}")
        return plan["payload"]["architecture"]["candidates"]
    if args.command == "execute-approved-plan":
        return client.request("POST", f"/api/v1/deployment-plans/{args.plan_id}/execute")
    if args.command == "get-environment-status":
        return client.request("GET", f"/api/v1/environments/{args.environment_id}")
    if args.command == "get-audit-events":
        suffix = f"?environment_id={args.environment_id}" if args.environment_id else ""
        return client.request("GET", f"/api/v1/audit-events{suffix}")
    if args.command == "destroy-environment":
        return client.request("POST", f"/api/v1/environments/{args.environment_id}/destroy-plan")
    raise ValueError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.token:
        raise SystemExit(
            "set AGENTCONSTRUCT_TOKEN or pass --token; the CLI never obtains cloud credentials"
        )
    result = run(args, ProductApiClient(args.api_url, args.token))
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
