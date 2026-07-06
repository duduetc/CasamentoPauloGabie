"""Rotas da página de presentes, modal HTMX e PIX."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import add_contribution, get_all_contributions_totals

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

GIFTS = [
    {
        "id": 1,
        "name": "Jogo de Panelas",
        "description": "Conjunto de panelas antiaderentes de alta qualidade",
        "price": 850.00,
        "image": "/static/images/gifts/panelas.jpg",
    },
    {
        "id": 2,
        "name": "KitchenAid",
        "description": "Batedeira planetária Stand Mixer 4,7L",
        "price": 2500.00,
        "image": "/static/images/gifts/kitchenaid.jpg",
    },
    {
        "id": 3,
        "name": "Jogo de Cama",
        "description": "Jogo de cama king 400 fios, 100% algodão egípcio",
        "price": 1200.00,
        "image": "/static/images/gifts/cama.jpg",
    },
    {
        "id": 4,
        "name": "Viagem de Lua de Mel",
        "description": "Contribuição para a viagem dos noivos",
        "price": 10000.00,
        "image": "/static/images/gifts/viagem.jpg",
    },
    {
        "id": 5,
        "name": "Adega de Vinhos",
        "description": "Adega climatizada para 12 garrafas",
        "price": 1800.00,
        "image": "/static/images/gifts/adega.jpg",
    },
    {
        "id": 6,
        "name": "Jogo de Toalhas",
        "description": "Kit 8 toalhas felpudas premium",
        "price": 480.00,
        "image": "/static/images/gifts/toalhas.jpg",
    },
    {
        "id": 7,
        "name": "Faqueiro Completo",
        "description": "Faqueiro em inox para receber familia e amigos",
        "price": 650.00,
        "image": "/static/images/gifts/panelas.jpg",
    },
    {
        "id": 8,
        "name": "Aparelho de Jantar",
        "description": "Conjunto de pratos rasos, fundos e de sobremesa para 6 pessoas",
        "price": 720.00,
        "image": "/static/images/gifts/panelas.jpg",
    },
    {
        "id": 9,
        "name": "Jogo de Copos",
        "description": "Copos de vidro para agua, suco e drinks do dia a dia",
        "price": 320.00,
        "image": "/static/images/gifts/adega.jpg",
    },
    {
        "id": 10,
        "name": "Jogo de Tacas",
        "description": "Tacas para vinho e espumante em ocasioes especiais",
        "price": 540.00,
        "image": "/static/images/gifts/adega.jpg",
    },
    {
        "id": 11,
        "name": "Travessas de Servir",
        "description": "Travessas elegantes para almocos, jantares e encontros em casa",
        "price": 430.00,
        "image": "/static/images/gifts/panelas.jpg",
    },
    {
        "id": 12,
        "name": "Jogo de Sobremesa",
        "description": "Pratos e bowls para sobremesas, frutas e cafe da tarde",
        "price": 360.00,
        "image": "/static/images/gifts/panelas.jpg",
    },
    {
        "id": 13,
        "name": "Edredom King",
        "description": "Edredom macio e aconchegante para a cama dos noivos",
        "price": 690.00,
        "image": "/static/images/gifts/cama.jpg",
    },
    {
        "id": 14,
        "name": "Travesseiros Premium",
        "description": "Par de travesseiros confortaveis para noites de descanso",
        "price": 380.00,
        "image": "/static/images/gifts/cama.jpg",
    },
    {
        "id": 15,
        "name": "Manta Decorativa",
        "description": "Manta para deixar o quarto e a sala mais acolhedores",
        "price": 290.00,
        "image": "/static/images/gifts/cama.jpg",
    },
    {
        "id": 16,
        "name": "Roupao do Casal",
        "description": "Par de roupao felpudo para momentos de conforto",
        "price": 520.00,
        "image": "/static/images/gifts/toalhas.jpg",
    },
    {
        "id": 17,
        "name": "Tapetes de Banheiro",
        "description": "Conjunto de tapetes macios e absorventes para o banheiro",
        "price": 260.00,
        "image": "/static/images/gifts/toalhas.jpg",
    },
    {
        "id": 18,
        "name": "Air Fryer",
        "description": "Fritadeira eletrica para receitas praticas na rotina do casal",
        "price": 780.00,
        "image": "/static/images/gifts/kitchenaid.jpg",
    },
    {
        "id": 19,
        "name": "Smart TV 55\"",
        "description": "Televisor Smart 55 polegadas com resolução 4K",
        "price": 3200.00,
        "image": "/static/images/gifts/tv.svg",
    },
    {
        "id": 20,
        "name": "Máquina de Café Espresso",
        "description": "Máquina de café espresso automática para o dia a dia",
        "price": 950.00,
        "image": "/static/images/gifts/cafe.svg",
    },
    {
        "id": 21,
        "name": "Conjunto de Facas",
        "description": "Conjunto profissional de facas para cozinha",
        "price": 380.00,
        "image": "/static/images/gifts/facas.svg",
    },
    {
        "id": 22,
        "name": "Mixer de Mão",
        "description": "Mixer de mão potente para preparar molhos e sopas",
        "price": 220.00,
        "image": "/static/images/gifts/mixer.svg",
    },
    {
        "id": 23,
        "name": "Conjunto de Panelas Tramontina",
        "description": "Conjunto de panelas em inox para o dia a dia",
        "price": 780.00,
        "image": "/static/images/gifts/panelas2.svg",
    },
    {
        "id": 24,
        "name": "Caixa de Experiência",
        "description": "Vale para jantar romântico ou experiência a escolher",
        "price": 450.00,
        "image": "/static/images/gifts/experiencia.svg",
    },
]

PIX_QR_CODE_IMG = "/static/images/pix_qr.png"
PIX_COPY_PASTE = "077.994.921-80"


def _gifts_with_contributions() -> list:
    totals = get_all_contributions_totals()
    return [
        {**g, "contributed": totals.get(g["id"], 0.0)}
        for g in GIFTS
    ]


@router.get("/presentes", response_class=HTMLResponse)
async def gifts_page(request: Request):
    return templates.TemplateResponse(
        "pages/gifts.html",
        {"request": request, "gifts": _gifts_with_contributions()},
    )


@router.get("/presentes/{gift_id}/modal", response_class=HTMLResponse)
async def gift_modal(request: Request, gift_id: int):
    gifts = _gifts_with_contributions()
    gift = next((g for g in gifts if g["id"] == gift_id), None)
    if not gift:
        return HTMLResponse("<p>Presente não encontrado.</p>", status_code=404)
    return templates.TemplateResponse(
        "partials/gift_modal.html",
        {
            "request": request,
            "gift": gift,
            "pix_qr": PIX_QR_CODE_IMG,
            "pix_code": PIX_COPY_PASTE,
        },
    )


@router.post("/presentes/{gift_id}/contribuir", response_class=HTMLResponse)
async def contribute(request: Request, gift_id: int, amount: float = Form(...)):
    gifts = _gifts_with_contributions()
    gift = next((g for g in gifts if g["id"] == gift_id), None)
    if not gift:
        return HTMLResponse("<p>Presente não encontrado.</p>", status_code=404)
    return templates.TemplateResponse(
        "partials/pix_payment.html",
        {
            "request": request,
            "gift": gift,
            "amount": amount,
            "pix_qr": PIX_QR_CODE_IMG,
            "pix_code": PIX_COPY_PASTE,
        },
    )


@router.post("/presentes/{gift_id}/confirmar", response_class=HTMLResponse)
async def confirm_contribution(
    request: Request,
    gift_id: int,
    name: str = Form(...),
    amount: float = Form(...),
    message: str = Form(""),
    gift_name: str = Form(""),
):
    add_contribution(
        gift_id=gift_id,
        gift_name=gift_name,
        contributor_name=name,
        amount=amount,
        message=message,
    )
    return templates.TemplateResponse(
        "partials/contribution_success.html",
        {
            "request": request,
            "gift_name": gift_name,
            "name": name,
            "amount": amount,
            "message": message,
        },
    )
