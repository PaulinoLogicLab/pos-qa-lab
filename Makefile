PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: install lint unit robot parallel device test up down logs docker-test clean

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m ruff check .

unit:
	$(PYTHON) -m pytest

robot:
	$(PYTHON) scripts/run_suite.py --exclude device

parallel:
	$(PYTHON) scripts/run_parallel.py --processes 4

device:
	$(PYTHON) scripts/run_suite.py --device --no-api

test: lint unit robot

up:
	$(COMPOSE) up -d api

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

docker-test:
	mkdir -p reports; chmod 777 reports 2>/dev/null || true; \
	$(COMPOSE) up --abort-on-container-exit --exit-code-from tests tests; \
	status=$$?; $(COMPOSE) down -v; exit $$status

clean:
	rm -rf reports/robot reports/pabot reports/device_run
