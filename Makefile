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