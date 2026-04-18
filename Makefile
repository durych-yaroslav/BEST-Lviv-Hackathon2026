.PHONY: up down frontend-up frontend-down backend-up backend-down reset

up:
	docker compose up -d --build

down:
	docker compose down

frontend-up:
	docker compose up -d --build frontend

frontend-down:
	docker compose down

backend-up:
	docker compose up -d --build backend

backend-down:
	docker compose stop backend

reset:
	docker compose down
	@python -c "import os; os.remove('backend/db.sqlite3') if os.path.exists('backend/db.sqlite3') else None"
	docker compose up -d --build
	@echo Waiting for database to start...
	@python -c "import time; time.sleep(5)"
	docker compose exec backend python manage.py migrate
