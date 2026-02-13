run:
	docker compose -f docker-compose.dev.yml up --build -d

up:	
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

down-v:
	docker compose -f docker-compose.dev.yml down -v

migrate: # docker exec backend-dev alembic revision --autogenerate -m ""
	docker exec -f backend-dev alembic upgrade head 

postgres:
	docker exec -it postgres-dev psql -U smart -d smart
