#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import uuid

import httpx

BASE = "http://127.0.0.1:8080"


def token(client: httpx.Client, username: str) -> str:
    return client.post(f"{BASE}/api/v1/auth/local-login", json={"username": username}).json()["access_token"]


def auth(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def wait_for_state(client: httpx.Client, token_value: str, environment_ids: set[str], expected: set[str]) -> list[dict]:
    for _ in range(60):
        environments = client.get(f"{BASE}/api/v1/environments", headers=auth(token_value)).json()
        selected = [item for item in environments if item["id"] in environment_ids]
        if len(selected) == len(environment_ids) and {item["state"] for item in selected} == expected:
            return selected
        time.sleep(0.25)
    raise AssertionError("worker did not observe the expected environment state")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure", action="store_true")
    parser.add_argument("--readiness-failure", action="store_true")
    parser.add_argument("--day2", action="store_true")
    args = parser.parse_args()
    with httpx.Client(timeout=15) as client:
        founder = token(client, "founder")
        repository = "https://github.com/example/support-rag-api"
        project = client.post(f"{BASE}/api/v1/projects", headers=auth(founder), json={"name": f"support-rag-{uuid.uuid4().hex[:8]}", "repository_url": repository}).json()
        prompt = "Deploy this AI API in AWS. Keep customer data private. Support 20 requests per second and peak at 100 requests per second. Keep monthly infrastructure under $1500. Create staging and production. Enable monitoring and Slack alerts."
        if args.failure:
            prompt = prompt.replace("under $1500", "under $2500")
        if args.readiness_failure:
            prompt = f"{prompt} Force failure so the bounded fixture reports a readiness failure."
        intent_response = client.post(f"{BASE}/api/v1/intents", headers=auth(founder), json={"project_id": project["id"], "prompt": prompt, "source_repository": repository, "idempotency_key": uuid.uuid4().hex})
        intent_response.raise_for_status()
        intent = intent_response.json()
        plan_response = client.post(f"{BASE}/api/v1/intents/{intent['id']}/plans", headers=auth(founder))
        plan_response.raise_for_status()
        plan = plan_response.json()
        if args.failure:
            assert plan["state"] == "POLICY_DENIED", plan
            print("failure demo passed: policy denied the over-budget request; nothing was executed")
            return
        assert plan["state"] == "APPROVAL_REQUIRED", plan
        operator = token(client, "operator")
        approval = client.post(f"{BASE}/api/v1/deployment-plans/{plan['id']}/approve", headers=auth(operator), json={"plan_hash": plan["plan_hash"]})
        approval.raise_for_status()
        result = client.post(f"{BASE}/api/v1/deployment-plans/{plan['id']}/execute", headers=auth(operator))
        result.raise_for_status()
        queued = result.json()["environments"]
        environments = wait_for_state(client, operator, {item["id"] for item in queued}, {"FAILED"} if args.readiness_failure else {"READY"})
        if args.readiness_failure:
            assert {item["state"] for item in environments} == {"FAILED"}, environments
            print("readiness-failure demo passed: the observer recorded FAILED; READY was not assumed")
            return
        assert {item["state"] for item in environments} == {"READY"}, environments
        production = next(item for item in environments if item["type"] == "production")
        if args.day2:
            recommendation_response = client.get(
                f"{BASE}/api/v1/environments/{production['id']}/recommendation",
                headers=auth(founder),
            )
            recommendation_response.raise_for_status()
            recommendation = recommendation_response.json()
            assert recommendation["evidence"]["queue_time_ms"] == 1200, recommendation
            change_response = client.post(
                f"{BASE}/api/v1/environments/{production['id']}/change-plan",
                headers=auth(founder),
            )
            change_response.raise_for_status()
            change = change_response.json()
            assert change["state"] == "APPROVAL_REQUIRED", change
            approved_change = client.post(
                f"{BASE}/api/v1/deployment-plans/{change['id']}/approve",
                headers=auth(operator),
                json={"plan_hash": change["plan_hash"]},
            )
            approved_change.raise_for_status()
            changed = client.post(
                f"{BASE}/api/v1/deployment-plans/{change['id']}/execute",
                headers=auth(operator),
            )
            changed.raise_for_status()
            updated = wait_for_state(client, operator, {production["id"]}, {"READY"})[0]
            assert updated["observed_state"]["p95_latency_ms"] == 1500, updated
        destroy = client.post(f"{BASE}/api/v1/environments/{production['id']}/destroy-plan", headers=auth(founder))
        destroy.raise_for_status()
        destroy_plan = destroy.json()
        approved_destroy = client.post(f"{BASE}/api/v1/deployment-plans/{destroy_plan['id']}/approve", headers=auth(operator), json={"plan_hash": destroy_plan["plan_hash"]})
        approved_destroy.raise_for_status()
        deleted = client.post(f"{BASE}/api/v1/deployment-plans/{destroy_plan['id']}/execute", headers=auth(operator))
        deleted.raise_for_status()
        destroyed_id = deleted.json()["environments"][0]["id"]
        assert wait_for_state(client, operator, {destroyed_id}, {"DESTROYED"})[0]["state"] == "DESTROYED"
        audit = client.get(f"{BASE}/api/v1/audit-events", headers=auth(founder)).json()
        assert any(event["action"] == "environment.destroyed" for event in audit)
        print(json.dumps({"success": "canonical demo passed", "day2_change": args.day2, "ready_environments": len(environments), "destroyed": production["id"], "audit_events": len(audit)}, indent=2))


if __name__ == "__main__":
    main()
