.PHONY: frontend-up frontend-down

frontend-up:
	docker compose up -d --build frontend

frontend-down:
	docker compose down

backend-up:
	docker compose up -d --build backend

backend-down:
	docker compose stop backend
