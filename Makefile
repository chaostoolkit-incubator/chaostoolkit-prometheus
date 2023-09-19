.PHONY: install
install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install -r requirements-dev.txt
	python3 setup.py develop

.PHONY: build
build:
	python3 setup.py build

.PHONY: lint
lint:
	ruff chaosprometheus/ tests/
	isort --check-only --profile black chaosprometheus/ tests/
	black --check --diff --line-length=80 chaosprometheus/ tests/

.PHONY: format
format:
	isort --profile black chaosprometheus/ tests/
	black --line-length=80 chaosprometheus/ tests/
	ruff chaosprometheus/ tests/ --fix

.PHONY: tests
tests:
	pytest
