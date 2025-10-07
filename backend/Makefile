.PHONY: dev run test lint migrate seed

# Development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest -v --cov=app --cov-report=html --cov-report=term-missing

# Lint code
lint:
	ruff check .
	ruff format .
	mypy app

# Run migrations
migrate:
	python -m alembic upgrade head

# Seed database (if needed)
seed:
	python -m app.init_db
	python -m app.init_user

# Generate alembic migration
migrate-make:
	python -m alembic revision --autogenerate -m "$(msg)"

# Install dependencies
install:
	pip install -r requirements.txt

# Install dev dependencies
install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

# Clean cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage

# Run all setup
setup: install-dev
	pip install -e .