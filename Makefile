PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
export PYTHONPATH := apps/api/src

.PHONY: install lint test bootstrap-local smoke demo demo-failure demo-readiness-failure trace-check browser-contract verify clean-local compose-logs opa-test terraform-validate kubernetes-render pilot-guardrails-plan pilot-cloud-plan pilot-cloud-apply pilot-cloud-push-image pilot-cloud-bootstrap-runtime pilot-cloud-smoke pilot-cloud-validate pilot-cloud-destroy

install:
	command -v $(PYTHON) >/dev/null || { echo "Python 3.12 is required"; exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e '.[dev]'

lint:
	$(PY) -m ruff check apps/api/src tests scripts

test:
	$(PY) -m pytest -q

bootstrap-local: install
	docker compose up -d --build

smoke:
	./scripts/smoke.sh

demo:
	$(PY) scripts/demo.py

demo-failure:
	$(PY) scripts/demo.py --failure

demo-readiness-failure:
	$(PY) scripts/demo.py --readiness-failure

trace-check:
	curl -fsS http://127.0.0.1:3200/ready >/dev/null
	curl -fsS 'http://127.0.0.1:3200/api/search?limit=1' | grep -q 'agentconstruct-api'
	@echo "Tempo received AgentConstruct traces."

browser-contract:
	./scripts/browser-contract.sh

opa-test:
	docker compose exec -T opa opa test /policies

terraform-validate:
	terraform fmt -check -recursive infrastructure/terraform
	terraform -chdir=infrastructure/terraform/bootstrap init -backend=false -input=false
	terraform -chdir=infrastructure/terraform/bootstrap validate
	terraform -chdir=infrastructure/terraform/pilot init -backend=false -input=false
	terraform -chdir=infrastructure/terraform/pilot validate

kubernetes-render:
	kubectl kustomize infrastructure/kubernetes/base >/dev/null
	@echo "Kubernetes contract rendered successfully. It was not applied to a cluster."

pilot-guardrails-plan:
	./scripts/pilot-cloud.sh guardrails-plan

pilot-cloud-plan:
	./scripts/pilot-cloud.sh plan

pilot-cloud-apply:
	./scripts/pilot-cloud.sh apply

pilot-cloud-push-image:
	./scripts/pilot-cloud.sh push-image

pilot-cloud-bootstrap-runtime:
	./scripts/pilot-cloud.sh bootstrap-runtime

pilot-cloud-smoke:
	./scripts/pilot-cloud.sh smoke

pilot-cloud-validate:
	./scripts/pilot-cloud.sh validate

pilot-cloud-destroy:
	./scripts/pilot-cloud.sh destroy

verify:
	$(MAKE) lint
	$(MAKE) test
	docker compose config --quiet

compose-logs:
	docker compose logs --no-color

clean-local:
	docker compose down -v --remove-orphans
	rm -rf $(VENV) .local
