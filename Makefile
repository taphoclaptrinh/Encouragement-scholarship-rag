.PHONY: setup demo eval test audit clean

PYTHON = python

setup:
	$(PYTHON) -m pip install -r requirements.txt
	@if not exist .env (copy .env.example .env)

demo:
	$(PYTHON) -m scripts.demo_runner

eval:
	$(PYTHON) -m tests.run_eval
	$(PYTHON) -m scripts.plot_metrics

test:
	$(PYTHON) -m pytest tests/

audit:
	$(PYTHON) -m scripts.external_auditor_client

clean:
	@if exist __pycache__ rd /s /q __pycache__
	@if exist .pytest_cache rd /s /q .pytest_cache
