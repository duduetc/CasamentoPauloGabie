"""Rotas da página de presentes, modal HTMX e exibição do PIX estático."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

GIFTS = [
    {
        "id": 1,
        "name": "Jogo de Panelas",
        "description": "Conjunto de panelas antiaderentes de alta qualidade",
        "price": 850.00,
        "image": "/static/images/gifts/panelas.jpg",
        "contributed": 0,
    },
    {
        "id": 2,
        "name": "KitchenAid",
        "description": "Batedeira planetária Stand Mixer 4,7L",
        "price": 2500.00,
        "image": "/static/images/gifts/kitchenaid.jpg",
        "contributed": 0,
    },
    {
        "id": 3,
        "name": "Jogo de Cama",
        "description": "Jogo de cama king 400 fios, 100% algodão egípcio",
        "price": 1200.00,
        "image": "/static/images/gifts/cama.jpg",
        "contributed": 600,
    },
    {
        "id": 4,
        "name": "Viagem de Lua de Mel",
        "description": "Contribuição para a viagem dos noivos",
        "price": 10000.00,
        "image": "/static/images/gifts/viagem.jpg",
        "contributed": 3000,
    },
    {
        "id": 5,
        "name": "Adega de Vinhos",
        "description": "Adega climatizada para 12 garrafas",
        "price": 1800.00,
        "image": "/static/images/gifts/adega.jpg",
        "contributed": 0,
    },
    {
        "id": 6,
        "name": "Jogo de Toalhas",
        "description": "Kit 8 toalhas felpudas premium",
        "price": 480.00,
        "image": "/static/images/gifts/toalhas.jpg",
        "contributed": 480,
    },
]

PIX_QR_CODE_IMG = "/static/images/pix_qr.png"
PIX_COPY_PASTE = (
    "00020126580014br.gov.bcb.pix0136example-key-uuid-here5204000053039865802BR"
    "5913Paulo e Gabie6009SAO PAULO62070503***6304ABCD"
)


@router.get("/presentes", response_class=HTMLResponse)
async def gifts_page(request: Request):
    return templates.TemplateResponse(
        "pages/gifts.html",
        {"request": request, "gifts": GIFTS},
    )


@router.get("/presentes/{gift_id}/modal", response_class=HTMLResponse)
async def gift_modal(request: Request, gift_id: int):
    gift = next((g for g in GIFTS if g["id"] == gift_id), None)
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
    gift = next((g for g in GIFTS if g["id"] == gift_id), None)
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
