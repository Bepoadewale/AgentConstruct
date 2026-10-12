PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
export PYTHONPATH := apps/api/src

.PHONY: install lint test bootstrap-local smoke seed-demo-data demo demo-simple demo-complex demo-day2 demo-degraded demo-failure demo-readiness-failure trace-check browser-contract customer-plan-e2e customer-plan-persistence verify clean-local compose-logs opa-test terraform-validate kubernetes-render mcp-local customer-aws-connection-plan customer-aws-connection-apply customer-aws-connection-destroy customer-aws-template-host-plan customer-aws-template-host-apply customer-aws-template-host-destroy pilot-guardrails-plan pilot-cloud-plan pilot-cloud-apply pilot-cloud-push-image pilot-cloud-bootstrap-runtime pilot-cloud-smoke pilot-cloud-validate pilot-cloud-destroy

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

seed-demo-data:
	$(PY) scripts/seed_demo_data.py

demo:
	$(PY) scripts/demo.py

demo-simple:
	$(PY) scripts/demo.py --simple

demo-complex:
	$(PY) scripts/demo.py --complex

demo-day2:
	$(PY) scripts/demo.py --day2

demo-degraded:
	$(PY) scripts/demo.py --degraded

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

customer-plan-e2e:
	$(PY) scripts/customer_plan_e2e.py

customer-plan-persistence:
	$(PY) scripts/customer_plan_e2e.py --verify-persistence

opa-test:
	docker compose exec -T opa opa test /policies

terraform-validate:
	terraform fmt -check -recursive infrastructure/terraform
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-bootstrap terraform -chdir=infrastructure/terraform/agentconstruct-bootstrap init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-bootstrap terraform -chdir=infrastructure/terraform/agentconstruct-bootstrap validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-foundation terraform -chdir=infrastructure/terraform/bootstrap init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-foundation terraform -chdir=infrastructure/terraform/bootstrap validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-management terraform -chdir=infrastructure/terraform/management-identity init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-management terraform -chdir=infrastructure/terraform/management-identity validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-runtime terraform -chdir=infrastructure/terraform/control-plane-runtime-identity init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-runtime terraform -chdir=infrastructure/terraform/control-plane-runtime-identity validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-connection terraform -chdir=infrastructure/terraform/customer-connection init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-connection terraform -chdir=infrastructure/terraform/customer-connection validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-template-host terraform -chdir=infrastructure/terraform/connection-template-host init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-template-host terraform -chdir=infrastructure/terraform/connection-template-host validate
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-pilot terraform -chdir=infrastructure/terraform/pilot init -backend=false -input=false
	TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-pilot terraform -chdir=infrastructure/terraform/pilot validate

customer-aws-connection-plan:
	./scripts/customer-aws-connection.sh plan

customer-aws-connection-apply:
	./scripts/customer-aws-connection.sh apply

customer-aws-connection-destroy:
	./scripts/customer-aws-connection.sh destroy

customer-aws-template-host-plan:
	./scripts/customer-aws-template-host.sh plan

customer-aws-template-host-apply:
	./scripts/customer-aws-template-host.sh apply

customer-aws-template-host-destroy:
	./scripts/customer-aws-template-host.sh destroy

kubernetes-render:
	kubectl kustomize infrastructure/kubernetes/base >/dev/null
	@echo "Kubernetes contract rendered successfully. It was not applied to a cluster."

mcp-local:
	@test -n "$$AGENTCONSTRUCT_TOKEN" || { echo "Set AGENTCONSTRUCT_TOKEN first; MCP never obtains cloud credentials."; exit 1; }
	$(VENV)/bin/agentconstruct-mcp

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
