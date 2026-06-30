# CasamentoGabrielaPaulo Isaque

## Como rodar localmente

Utilize o arquivo `Makefile` para rodar o servidor. Caso não funcione, execute os comandos abaixo manualmente:

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Inicie o servidor (da raiz do projeto)
```bash
uvicorn app.main:app --reload
```

### 3. Acesse no navegador

- Página principal: http://localhost:8000
- Lista de presentes: http://localhost:8000/presentes
