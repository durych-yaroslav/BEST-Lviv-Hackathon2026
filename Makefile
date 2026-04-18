.PHONY: up down frontend-up frontend-down backend-up backend-down

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
