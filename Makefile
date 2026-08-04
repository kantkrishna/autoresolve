.PHONY: install test lint clean

install:
	poetry install
	poetry run pre-commit install

test:
	poetry run pytest tests/

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run mypy src/

clean:
	# Note: These are Unix commands. If you are using standard Windows CMD, 
	# this specific 'clean' command might fail. Use Git Bash or WSL if needed.
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache

reset:
	poetry run python scripts/force-reset-lab.py

rebuild:
	poetry run python scripts/soft-rebuild-lab.py

wake:
	poetry run python scripts/wake-up-lab.py

tunnels:
	poetry run python scripts/start_tunnels.py

workflow:
	poetry run python scripts/incident_workflow.py