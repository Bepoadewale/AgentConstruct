PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
export PYTHONPATH := apps/api/src

.PHONY: install lint test bootstrap-local smoke demo demo-failure demo-readiness-failure trace-check verify clean-local compose-logs opa-test terraform-validate

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

opa-test:
	docker compose exec -T opa opa test /policies

terraform-validate:
	@echo "AWS Terraform is a roadmap interface for this V1 foundation; no cloud root exists yet."

verify:
	$(MAKE) lint
	$(MAKE) test
	docker compose config --quiet

compose-logs:
	docker compose logs --no-color

clean-local:
	docker compose down -v --remove-orphans
	rm -rf $(VENV) .local
