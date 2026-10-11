"""Deterministic two-user proof for the customer-plan decision workflow.

This uses separate HTTP clients as the local developer and administrator browser
sessions would. It deliberately exercises only planning and decision endpoints;
it never calls the deployment executor.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8080"
PROMPT = (
    "Deploy this small containerized FastAPI AI API in AWS. Support 2 requests per second "
    "and peak at 10 requests per second. Keep monthly infrastructure under $300. "
    "Create staging and production. Enable monitoring."
)


def token(client: httpx.Client, username: str) -> str:
    response = client.post(f"{BASE}/api/v1/auth/local-login", json={"username": username})
    response.raise_for_status()
    return response.json()["access_token"]


def auth(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def expect(response: httpx.Response, status: int, description: str) -> dict:
    if response.status_code != status:
        raise AssertionError(f"{description}: expected {status}, got {response.status_code}: {response.text}")
    return response.json()


def create_review(client: httpx.Client, actor: str, label: str) -> dict:
    suffix = f"{label}-{uuid.uuid4().hex[:8]}"
    repository = f"https://github.com/example/{label}"
    project = expect(
        client.post(
            f"{BASE}/api/v1/projects",
            headers=auth(actor),
            json={"name": suffix, "repository_url": repository, "repository_branch": "main"},
        ),
        201,
        "create project",
    )
    intent = expect(
        client.post(
            f"{BASE}/api/v1/intents",
            headers=auth(actor),
            json={
                "project_id": project["id"],
                "prompt": PROMPT,
                "source_repository": repository,
                "idempotency_key": suffix,
            },
        ),
        201,
        "create intent",
    )
    deployment = expect(
        client.post(f"{BASE}/api/v1/intents/{intent['id']}/plans", headers=auth(actor)),
        201,
        "create deployment recommendation",
    )
    review = expect(
        client.post(
            f"{BASE}/api/v1/deployment-plans/{deployment['id']}/customer-review",
            headers=auth(actor),
        ),
        201,
        "create customer review",
    )
    assert review["state"] == "DRAFT"
    assert review["content"]["summary"]["selected_profile"] == "aws-app-runner"
    observability = review["content"]["observability"]
    assert observability["metrics_backend"].startswith("Prometheus")
    assert observability["dashboard"] == "Amazon Managed Grafana"
    return review


def submit(client: httpx.Client, actor: str, revision_id: str) -> dict:
    review = expect(
        client.post(
            f"{BASE}/api/v1/customer-plan-revisions/{revision_id}/submit", headers=auth(actor)
        ),
        200,
        "submit customer review",
    )
    assert review["state"] == "SUBMITTED"
    assert review["execution"] == "UNEXECUTED_APPROVAL_ONLY"
    return review


def decide(
    client: httpx.Client, actor: str, review: dict, decision: str, reason: str | None = None
) -> httpx.Response:
    payload = {"decision": decision, "content_digest": review["content_digest"]}
    if reason:
        payload["reason"] = reason
    return client.post(
        f"{BASE}/api/v1/customer-plan-revisions/{review['id']}/decisions",
        headers=auth(actor),
        json=payload,
    )


def run(state_file: Path) -> None:
    with httpx.Client(timeout=15) as client:
        developer = token(client, "founder")
        administrator = token(client, "administrator")
        other_tenant = token(client, "other-tenant")

        developer_review = submit(
            client, developer, create_review(client, developer, "developer-approval")["id"]
        )
        assert decide(client, developer, developer_review, "APPROVED").status_code == 403
        assert decide(client, administrator, {**developer_review, "content_digest": "0" * 64}, "APPROVED").status_code == 409
        approved = expect(decide(client, administrator, developer_review, "APPROVED"), 200, "admin approval")
        assert approved["state"] == "APPROVED"
        assert approved["decision"]["is_self_approval"] is False
        assert decide(client, administrator, approved, "APPROVED").status_code == 409
        assert client.get(
            f"{BASE}/api/v1/customer-plan-revisions/{approved['id']}", headers=auth(other_tenant)
        ).status_code == 403

        rejected = submit(
            client, developer, create_review(client, developer, "developer-rejection")["id"]
        )
        rejected = expect(
            decide(client, administrator, rejected, "REJECTED", "Use a lower-risk data store."),
            200,
            "admin rejection",
        )
        assert rejected["state"] == "REJECTED"
        assert rejected["decision"]["reason"] == "Use a lower-risk data store."
        revised = expect(
            client.post(
                f"{BASE}/api/v1/customer-plans/{rejected['plan_id']}/revisions",
                headers=auth(developer),
                json={"content": rejected["content"]},
            ),
            201,
            "create revised draft",
        )
        assert revised["revision"] == 2 and revised["state"] == "DRAFT"

        admin_review = submit(
            client, administrator, create_review(client, administrator, "admin-self-approval")["id"]
        )
        self_approved = expect(
            decide(client, administrator, admin_review, "APPROVED"), 200, "administrator self-approval"
        )
        assert self_approved["state"] == "APPROVED"
        assert self_approved["decision"]["is_self_approval"] is True
        assert self_approved["decision"]["authorization_policy"] == "workspace-administrator-self-approval-allowed"

        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            json.dumps({"revision_id": approved["id"], "expected_state": "APPROVED"}) + "\n"
        )
        print("customer-plan E2E passed: developer approval, rejection/revision, and administrator self-approval")


def verify_persistence(state_file: Path) -> None:
    state = json.loads(state_file.read_text())
    with httpx.Client(timeout=15) as client:
        developer = token(client, "founder")
        review = expect(
            client.get(
                f"{BASE}/api/v1/customer-plan-revisions/{state['revision_id']}", headers=auth(developer)
            ),
            200,
            "read persisted customer review",
        )
    assert review["state"] == state["expected_state"]
    assert review["execution"] == "UNEXECUTED_APPROVAL_ONLY"
    print("customer-plan persistence check passed after API restart")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=".local/customer-plan-e2e.json")
    parser.add_argument("--verify-persistence", action="store_true")
    args = parser.parse_args()
    state_file = Path(args.state_file)
    if args.verify_persistence:
        verify_persistence(state_file)
    else:
        run(state_file)


if __name__ == "__main__":
    main()
