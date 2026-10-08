#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import uuid

import httpx

BASE = "http://127.0.0.1:8080"


def token(client: httpx.Client, username: str) -> str:
    return client.post(f"{BASE}/api/v1/auth/local-login", json={"username": username}).json()["access_token"]


def auth(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure", action="store_true")
    args = parser.parse_args()
    with httpx.Client(timeout=15) as client:
        founder = token(client, "founder")
        repository = "https://github.com/example/support-rag-api"
        project = client.post(f"{BASE}/api/v1/projects", headers=auth(founder), json={"name": f"support-rag-{uuid.uuid4().hex[:8]}", "repository_url": repository}).json()
        prompt = "Deploy this AI API in AWS. Keep customer data private. Support 20 requests per second and peak at 100 requests per second. Keep monthly infrastructure under $1500. Create staging and production. Enable monitoring and Slack alerts."
        if args.failure:
            prompt = prompt.replace("under $1500", "under $2500")
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
        environments = result.json()["environments"]
        assert {item["state"] for item in environments} == {"READY"}, environments
        production = next(item for item in environments if item["type"] == "production")
        destroy = client.post(f"{BASE}/api/v1/environments/{production['id']}/destroy-plan", headers=auth(founder))
        destroy.raise_for_status()
        destroy_plan = destroy.json()
        approved_destroy = client.post(f"{BASE}/api/v1/deployment-plans/{destroy_plan['id']}/approve", headers=auth(operator), json={"plan_hash": destroy_plan["plan_hash"]})
        approved_destroy.raise_for_status()
        deleted = client.post(f"{BASE}/api/v1/deployment-plans/{destroy_plan['id']}/execute", headers=auth(operator))
        deleted.raise_for_status()
        assert deleted.json()["environments"][0]["state"] == "DESTROYED", deleted.json()
        audit = client.get(f"{BASE}/api/v1/audit-events", headers=auth(founder)).json()
        assert any(event["action"] == "environment.destroyed" for event in audit)
        print(json.dumps({"success": "canonical demo passed", "ready_environments": len(environments), "destroyed": production["id"], "audit_events": len(audit)}, indent=2))


if __name__ == "__main__":
    main()
