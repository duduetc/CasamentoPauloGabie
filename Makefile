.PHONY: install run help

# Comando padrão ao rodar apenas "make"
default: help

help:
	@echo "============================================"
	@echo "  Comandos disponíveis:"
	@echo "============================================"
	@echo "  make install   -> Instala as dependências"
	@echo "  make run       -> Inicia o servidor"
	@echo "  make start     -> Instala + inicia o servidor"
	@echo "============================================"

install:
	@echo "Instalando dependências..."
	pip install -r requirements.txt

run:
	@echo "Iniciando servidor..."
	@echo "Acesse:"
	@echo "  - Página principal : http://localhost:8000"
	@echo "  - Lista presentes  : http://localhost:8000/presentes"
	uvicorn app.main:app --reload

start: install run
