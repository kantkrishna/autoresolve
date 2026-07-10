.PHONY: install test lint clean
install:
    pip install pre-commit pytest ruff black mypy
    pre-commit install

test:
	pytest tests/

lint:
	ruff check .
	black --check .
	mypy src/

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .ruff_cache .mypy_cache
	