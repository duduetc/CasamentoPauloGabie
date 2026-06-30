# 📁 Estrutura do Projeto — CasamentoPauloGabie

Site de casamento de **Paulo & Gabie**, construído com **FastAPI** + **Jinja2** + **HTMX**.

---

## 🗂️ Visão Geral

```
CasamentoPauloGabie/
│
├── app/                        ← Código-fonte principal da aplicação
│   ├── main.py                 ← Ponto de entrada: cria o app FastAPI e registra as rotas
│   │
│   ├── routes/                 ← Controladores HTTP (recebem requisições e retornam respostas)
│   │   ├── __init__.py
│   │   ├── admin.py            ← Rotas da área administrativa
│   │   ├── gifts.py            ← Rotas da lista de presentes e modal de contribuição via PIX
│   │   ├── public.py           ← Rotas públicas (página inicial, etc.)
│   │   └── rsvp.py             ← Rotas do formulário de confirmação de presença (RSVP)
│   │
│   ├── repositories/           ← Camada de acesso a dados (onde os dados seriam lidos/gravados)
│   │   ├── __init__.py
│   │   ├── contributions.py    ← Repositório de contribuições aos presentes
│   │   ├── gifts.py            ← Repositório dos presentes da lista
│   │   ├── guests.py           ← Repositório dos convidados
│   │   └── settings.py         ← Repositório das configurações gerais do site
│   │
│   ├── schemas/                ← Modelos de dados (estrutura/validação dos objetos)
│   │   ├── __init__.py
│   │   ├── contribution.py     ← Schema de uma contribuição (quem contribuiu, quanto, para qual presente)
│   │   ├── gift.py             ← Schema de um presente (nome, preço, imagem, etc.)
│   │   ├── guest.py            ← Schema de um convidado (nome, confirmação, mesa, etc.)
│   │   └── site.py             ← Schema das configurações do site (data, local, etc.)
│   │
│   ├── services/               ← Regras de negócio (lógica entre as rotas e os repositórios)
│   │   ├── __init__.py
│   │   ├── content.py          ← Serviço de conteúdo do site
│   │   ├── gifts.py            ← Serviço dos presentes (cálculos de contribuição, etc.)
│   │   ├── rsvp.py             ← Serviço de RSVP (processar confirmações de presença)
│   │   └── theme.py            ← Serviço de tema visual do site
│   │
│   ├── static/                 ← Arquivos estáticos servidos diretamente ao navegador
│   │   ├── css/
│   │   │   └── theme.css       ← Estilos globais / tema visual do site
│   │   ├── js/
│   │   │   └── ui.js           ← Scripts de interatividade do front-end
│   │   └── images/
│   │       ├── MELQ5754.jpg    ← Imagem principal do casal (banner)
│   │       ├── MELQ4642.jpg    ← Foto do casal 1
│   │       ├── MELQ5044.jpg    ← Foto do casal 2
│   │       ├── MELQ5989.jpg    ← Foto do casal 3
│   │       ├── pix_qr.png      ← QR Code PIX para contribuições
│   │       └── gifts/          ← Imagens individuais de cada presente da lista
│   │
│   └── templates/              ← Templates HTML renderizados pelo Jinja2
│       ├── base.html           ← Template base (header, footer, links de CSS/JS compartilhados)
│       ├── pages/              ← Páginas completas do site
│       │   ├── home.html       ← Página inicial (hero, casal, informações do casamento)
│       │   ├── gifts.html      ← Página da lista de presentes
│       │   ├── admin.html      ← Página administrativa
│       │   ├── rsvp.html       ← Página do formulário de RSVP
│       │   └── seat.html       ← Página de mapa/assentos
│       └── partials/           ← Fragmentos HTML carregados dinamicamente via HTMX
│           ├── gift_modal.html     ← Modal de detalhes de um presente (aberto ao clicar)
│           ├── pix_payment.html    ← Tela de pagamento PIX após escolher contribuição
│           ├── rsvp_form.html      ← Formulário parcial de RSVP
│           ├── rsvp_success.html   ← Mensagem de sucesso após confirmar presença
│           └── seat_card.html      ← Card de assento individual
│
├── .gitignore                  ← Lista de arquivos/pastas ignorados pelo Git (ex: __pycache__, .env)
├── Makefile                    ← Atalhos de terminal: `make install`, `make run`, `make start`
├── README.md                   ← Apresentação do projeto (como instalar e rodar)
├── ESTRUTURA.md                ← Este arquivo — guia da estrutura do projeto
└── requirements.txt            ← Dependências Python do projeto
```

---

## 🧠 Arquitetura em Camadas

O projeto segue o padrão de **separação de responsabilidades** (camadas), comum em APIs web:

| Camada | Pasta | Responsabilidade |
|---|---|---|
| **Rotas** | `routes/` | Receber a requisição HTTP e retornar a resposta correta |
| **Serviços** | `services/` | Conter a lógica de negócio (ex: calcular contribuições) |
| **Repositórios** | `repositories/` | Acessar e persistir dados |
| **Schemas** | `schemas/` | Definir e validar a estrutura dos dados |
| **Templates** | `templates/` | Renderizar o HTML que o usuário vê no navegador |

---

## ⚡ Stack Tecnológica

| Tecnologia | Papel |
|---|---|
| **FastAPI** | Framework web Python — gerencia as rotas e requisições |
| **Uvicorn** | Servidor ASGI — executa a aplicação FastAPI |
| **Jinja2** | Motor de templates — renderiza os arquivos HTML |
| **HTMX** | Biblioteca JS — permite requisições dinâmicas sem recarregar a página |
| **python-multipart** | Permite receber formulários HTML via POST |
| **aiofiles** | Leitura/escrita assíncrona de arquivos |

---

## 🚀 Como Rodar o Projeto

```bash
# Instalar dependências e iniciar o servidor
make start

# Ou separadamente:
make install   # Instala as dependências do requirements.txt
make run       # Inicia o servidor em http://localhost:8000
```

| URL | Descrição |
|---|---|
| `http://localhost:8000` | Página inicial do site |
| `http://localhost:8000/presentes` | Lista de presentes com contribuição via PIX |

---

## 🎁 Fluxo Principal — Lista de Presentes

```
Usuário acessa /presentes
        ↓
gifts.py (route) → renderiza pages/gifts.html com a lista de GIFTS
        ↓
Usuário clica em um presente
        ↓
HTMX faz GET /presentes/{id}/modal → retorna partials/gift_modal.html
        ↓
Usuário digita um valor e confirma
        ↓
HTMX faz POST /presentes/{id}/contribuir → retorna partials/pix_payment.html
        ↓
Usuário vê o QR Code PIX e o código copia-e-cola
```
