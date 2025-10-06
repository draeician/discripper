.PHONY: install lint test format

install:
	python -m pip install -e .

lint:
	ruff check .

test:
	pytest

format:
	ruff format .
