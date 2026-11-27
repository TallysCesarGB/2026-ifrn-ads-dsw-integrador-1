# Atalhos para o ambiente local com Docker (equivalente ao justfile, sem
# precisar instalar o just). Uso: `make local` sobe tudo; `make` lista os alvos.

export COMPOSE_FILE := docker-compose.local.yml

COMPOSE := docker compose
MANAGE := $(COMPOSE) run --rm django python ./manage.py
URL := http://localhost:8000

.DEFAULT_GOAL := help
.PHONY: help local check build up down restart logs migrate demo seed test manage shell

help: ## Lista os comandos disponíveis
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

local: check build up migrate ## Sobe o ambiente completo (build, containers, migrations e dados demo)
	@if [ "$$($(MANAGE) shell -c 'from django.contrib.auth import get_user_model; print(get_user_model().objects.count())' 2>/dev/null | tail -1)" = "0" ]; then \
		echo "Banco vazio: carregando dados de demonstração..."; \
		$(MANAGE) loaddata fixtures/demo_data.json; \
	fi
	@echo ""
	@echo "Pronto: $(URL)"
	@echo "Login demo: demo@cineclub.com / cineclub123"
	@echo "Logs: make logs   |   Parar: make down"

check: ## Confere se o Docker está rodando e se a chave da TMDB existe
	@docker info >/dev/null 2>&1 || { echo "Docker não está rodando. Abra o Docker Desktop e tente de novo."; exit 1; }
	@test -f .envs/.local/.tmdb || { echo "Falta .envs/.local/.tmdb. Rode: cp .envs/.local/.tmdb.example .envs/.local/.tmdb e preencha TMDB_API_KEY."; exit 1; }
	@test -z "$$DATABASE_URL" || echo "Aviso: DATABASE_URL está definida no seu terminal; o container ignora, mas o Django fora do Docker vai usá-la."

build: ## Builda as imagens
	$(COMPOSE) build

up: ## Sobe os containers em segundo plano e espera o Postgres aceitar conexões
	$(COMPOSE) up -d --remove-orphans
	@echo "Aguardando o Postgres..."
	@for i in $$(seq 1 30); do \
		if [ "$$($(COMPOSE) ps -a --format '{{.State}}' postgres)" = "exited" ]; then \
			$(COMPOSE) logs --tail 15 postgres; \
			echo ""; \
			echo "O Postgres parou ao iniciar (logs acima). Se a mensagem for sobre dados de"; \
			echo "outra versão em /var/lib/postgresql, veja 'Problemas comuns' no README."; \
			exit 1; \
		fi; \
		$(COMPOSE) exec -T postgres pg_isready -q >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo "O Postgres não respondeu em 30s. Veja: make logs s=postgres"; exit 1

down: ## Derruba os containers (mantém o banco)
	$(COMPOSE) down

restart: ## Reinicia o container do Django
	$(COMPOSE) restart django

logs: ## Logs em tempo real (ex.: make logs s=django)
	$(COMPOSE) logs -f $(s)

migrate: ## Aplica as migrations
	$(MANAGE) migrate

demo: ## Carrega a fixture de demonstração (sobrescreve os registros dela)
	$(MANAGE) loaddata fixtures/demo_data.json

seed: ## Gera dados falsos com o seed_demo_data
	$(MANAGE) seed_demo_data

test: ## Roda os testes (ex.: make test a="films -x")
	$(COMPOSE) run --rm django pytest $(a)

manage: ## Qualquer comando do manage.py (ex.: make manage a=createsuperuser)
	$(MANAGE) $(a)

shell: ## Abre o shell do Django
	$(MANAGE) shell
