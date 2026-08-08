.PHONY: install migrate run test lint audit format compose-up compose-down superuser

install:
	python -m pip install -r requirements.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver

test:
	pytest

lint:
	ruff check .
	flake8 .

audit:
	python scripts/audit_project.py

format:
	ruff format .

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

superuser:
	docker compose exec web python manage.py createsuperuser
