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
	@# Використовуємо rm -f, що працює в git bash / mingw на Windows
	rm -f backend/db.sqlite3
	docker compose up -d --build
	@# Очікуємо 2 секунди, поки контейнер прокинеться
	sleep 2
	docker compose exec backend python manage.py migrate
