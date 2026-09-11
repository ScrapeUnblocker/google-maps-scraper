.PHONY: install lint format test run clean

install:
	python -m pip install -e ".[dev]"
	pre-commit install || true

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest -q

run:
	google-maps-scraper "coffee shops in chicago" --country US

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
