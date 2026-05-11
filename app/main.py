from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ─── In-memory gift list (replace with DB as needed) ───────────────────────
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

# Fake PIX QR code (base64 placeholder — replace with real image)
PIX_QR_CODE_IMG = "/static/images/pix_qr.png"
PIX_COPY_PASTE = "00020126580014br.gov.bcb.pix0136example-key-uuid-here5204000053039865802BR5913Paulo e Gabie6009SAO PAULO62070503***6304ABCD"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/presentes", response_class=HTMLResponse)
async def gifts_page(request: Request):
    return templates.TemplateResponse(
        "gifts.html", {"request": request, "gifts": GIFTS}
    )


@app.get("/presentes/{gift_id}/modal", response_class=HTMLResponse)
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


@app.post("/presentes/{gift_id}/contribuir", response_class=HTMLResponse)
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
