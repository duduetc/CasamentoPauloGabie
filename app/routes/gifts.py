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
        "name": "Microondas",
        "description": "Forno de micro=ondas com diversas funções",
        "price": 750.00,
        "image": "/static/images/gifts/microondas.jpg",
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
        "name": "Panela de Pressão",
        "description": "Panela de pressão elétrica com diversas funções",
        "price": 450.00,
        "image": "/static/images/gifts/paneladepressao.jpg",
    },
    {
        "id": 5,
        "name": "Processador de Alimentos",
        "description": "Processador de alimentos para preparar refeições deliciosas",
        "price": 450.00,
        "image": "/static/images/gifts/processador.jpg",
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
        "name": "Jarra de Vidro",
        "description": "Jarra de vidro para servir bebidas",
        "price": 80.00,
        "image": "/static/images/gifts/jarra_de_vidro.webp",
    },
    {
        "id": 8,
        "name": "Aparelho de Jantar",
        "description": "Conjunto de pratos rasos, fundos e de sobremesa para 6 pessoas",
        "price": 720.00,
        "image": "/static/images/gifts/pratos.jpg",
    },
    {
        "id": 9,
        "name": "Jogo de Copos",
        "description": "Copos de vidro para agua, suco e drinks do dia a dia",
        "price": 320.00,
        "image": "/static/images/gifts/copos.jpg",
    },
    {
        "id": 10,
        "name": "Jogo de Taças",
        "description": "Taças para vinho e espumante em ocasioes especiais",
        "price": 540.00,
        "image": "/static/images/gifts/tacas.jpg",
    },
    {
        "id": 11,
        "name": "Travessas de Servir",
        "description": "Travessas elegantes para almocos, jantares e encontros em casa",
        "price": 430.00,
        "image": "/static/images/gifts/travessas.jpg",
    },
    {
        "id": 12,
        "name": "Jogo de Sobremesa",
        "description": "Pratos e bowls para sobremesas, frutas e cafe da tarde",
        "price": 360.00,
        "image": "/static/images/gifts/sobremesa.jpg",
    },
    {
        "id": 13,
        "name": "Edredom King",
        "description": "Edredom macio e aconchegante para a cama dos noivos",
        "price": 690.00,
        "image": "/static/images/gifts/edredom.jpg",
    },
    {
        "id": 14,
        "name": "Travesseiros Premium",
        "description": "Par de travesseiros confortaveis para noites de descanso",
        "price": 380.00,
        "image": "/static/images/gifts/travesseiros.jpg",
    },
    {
        "id": 15,
        "name": "Manta Decorativa",
        "description": "Manta para deixar o quarto e a sala mais acolhedores",
        "price": 290.00,
        "image": "/static/images/gifts/manta.jpg",
    },
    {
        "id": 16,
        "name": "Roupao do Casal",
        "description": "Par de roupao felpudo para momentos de conforto",
        "price": 520.00,
        "image": "/static/images/gifts/roupao.jpg",
    },
    {
        "id": 17,
        "name": "Tapetes de Banheiro",
        "description": "Conjunto de tapetes macios e absorventes para o banheiro",
        "price": 260.00,
        "image": "/static/images/gifts/tapetes_banheiro.jpg",
    },
    {
        "id": 18,
        "name": "Air Fryer",
        "description": "Fritadeira eletrica para receitas praticas na rotina do casal",
        "price": 780.00,
        "image": "/static/images/gifts/air_fryer.jpg",
    },
    {
        "id": 19,
        "name": "Smart TV 55\"",
        "description": "Televisor Smart 55 polegadas com resolução 4K",
        "price": 3200.00,
        "image": "/static/images/gifts/tv.jpg",
    },
    {
        "id": 20,
        "name": "Máquina de Café Espresso",
        "description": "Máquina de café espresso automática para o dia a dia",
        "price": 950.00,
        "image": "/static/images/gifts/cafe.jpg",
    },
    {
        "id": 21,
        "name": "Conjunto de Facas",
        "description": "Conjunto profissional de facas para cozinha",
        "price": 380.00,
        "image": "/static/images/gifts/conjunto_facas.jpg",
    },
    {
        "id": 22,
        "name": "Mixer de Mão",
        "description": "Mixer de mão potente para preparar molhos e sopas",
        "price": 220.00,
        "image": "/static/images/gifts/mixer.jpg",
    },
    {
        "id": 23,
        "name": "Conjunto de Panelas Tramontina",
        "description": "Conjunto de panelas em inox para o dia a dia",
        "price": 780.00,
        "image": "/static/images/gifts/panelas2.jpg",
    },
    {
        "id": 24,
        "name": "Liquidificador",
        "description": "Eletrodoméstico essencial para o dia a dia, moderno e robusto.",
        "price": 450.00,
        "image": "/static/images/gifts/liquidificador.jpg",
    },
    {
        "id": 25,
        "name": "Forma para bolo",
        "description": "Forma para bolo de silicone para preparar doces deliciosos",
        "price": 60.00,
        "image": "/static/images/gifts/forma_bolo.jpg",
    },
    {
        "id": 26,
        "name": "Forma para pão",
        "description": "Forma para pão de silicone para preparar pães caseiros",
        "price": 50.00,
        "image": "/static/images/gifts/forma_pao.webp",
    },
    {
        "id": 27,
        "name": "Kit Assadeira de Vidro",
        "description": "Kit de assadeiras de vidro para preparar receitas no forno",
        "price": 120.00,
        "image": "/static/images/gifts/kit_assadeira.jpg",
    },
    {
        "id": 28,
        "name": "Chaleira Elétrica",
        "description": "Chaleira elétrica para preparar chá e café",
        "price": 180.00,
        "image": "/static/images/gifts/chaleira.jpg",
    },
    {
        "id": 29,
        "name": "Centrífuga de Saladas",
        "description": "Centrífuga para preparar saladas e sucos",
        "price": 90.00,
        "image": "/static/images/gifts/centrifuga.jpg",
    },
    {
        "id": 30,
        "name": "Moedor de Temperos",
        "description": "Moedor de temperos para preparar especiarias caseiras",
        "price": 80.00,
        "image": "/static/images/gifts/moedor_temperos.jpg",
    },
    {
        "id": 31,
        "name": "Kit de potes herméticos",
        "description": "Kit de potes herméticos para armazenar alimentos",
        "price": 180.00,
        "image": "/static/images/gifts/kit_potes.jpg",
    },
    {
        "id": 32,
        "name": "Porta-temperos",
        "description": "Porta-temperos para organizar a cozinha",
        "price": 150.00,
        "image": "/static/images/gifts/porta_temperos.jpg",
    },
    {
        "id": 33,
        "name": "Escorredor de louças inox",
        "description": "Escorredor de louças em aço inox para secar utensílios de cozinha",
        "price": 220.00,
        "image": "/static/images/gifts/escorredor_loucas.jpg",
    },
    {
        "id": 34,
        "name": "Lixeira Inox",
        "description": "Lixeira de aço inox para cozinha",
        "price": 220.00,
        "image": "/static/images/gifts/lixeira_inox.jpg",
    },
    {
        "id": 35,
        "name": "Tábuas de corte",
        "description": "Tábuas de corte em madeira para preparar alimentos",
        "price": 150.00,
        "image": "/static/images/gifts/tabuas_corte.jpg",
    },
    {
        "id": 36,
        "name": "Ralador multifuncional",
        "description": "Ralador multifuncional para preparar ingredientes",
        "price": 90.00,
        "image": "/static/images/gifts/ralador_multifuncional.jpg",
    },
    {
        "id": 37,
        "name": "Kit de Espátulas de Silicone",
        "description": "Kit de espátulas de silicone para preparar alimentos",
        "price": 100.00,
        "image": "/static/images/gifts/kit_espatulas.webp",
    },
    {
        "id": 38,
        "name": "Porta Guardanapos",
        "description": "Porta guardanapos para organizar a cozinha",
        "price": 80.00,
        "image": "/static/images/gifts/porta_guardanapos.jpg",
    },
    {
        "id": 39,
        "name": "Fruteira",
        "description": "Fruteira para organizar frutas e legumes",
        "price": 180.00,
        "image": "/static/images/gifts/fruteira.jpg",
    },
    {
        "id": 40,
        "name": "Cesto de Roupas",
        "description": "Cesto de roupas para organizar a lavanderia",
        "price": 180.00,
        "image": "/static/images/gifts/cesto_roupas.jpg",
    },
    {
        "id": 41,
        "name": "Varal de Chão",
        "description": "Varal de chão para secar roupas",
        "price": 180.00,
        "image": "/static/images/gifts/varal_chao.jpg",
    },
    {
        "id": 42,
        "name": "Vaporizador de roupas",
        "description": "Vaporizador de roupas para alisar tecidos",
        "price": 350.00,
        "image": "/static/images/gifts/vaporizador_roupas.jpg",
    },
    {
        "id": 43,
        "name": "Cabides de Veludo",
        "description": "50 unidades de cabides de veludo para organizar a roupa",
        "price": 150.00,
        "image": "/static/images/gifts/cabides_veludo.jpg",
    },
    {
        "id": 44,
        "name": "Caixas Organizadoras",
        "description": "Caixas organizadoras para armazenar itens na cozinha",
        "price": 100.00,
        "image": "/static/images/gifts/caixas_organizadoras.jpg",
    },
    {
        "id": 45,
        "name": "Almofadas Decorativas",
        "description": "Kit de almofadas decorativas para complementar a decoração da casa",
        "price": 180.00,
        "image": "/static/images/gifts/almofadas_decorativas.jpg",
    },
    {
        "id": 46,
        "name": "Capas para travesseiros",
        "description": "Conjunto de capas para travesseiros para complementar a decoração da casa",
        "price": 90.00,
        "image": "/static/images/gifts/capas_travesseiros.jpg",
    },
    {
        "id": 47,
        "name": "Difusor de Aromas",
        "description": "Difusor de aromas para perfumdar o ambiente",
        "price": 180.00,
        "image": "/static/images/gifts/difusor_aromas.jpg",
    },
    {
        "id": 48,
        "name": "Acessórios de Banheiro",
        "description": "Conjunto de acessórios de banheiro para complementar a decoração da casa",
        "price": 180.00,
        "image": "/static/images/gifts/acessorios_banheiro.jpg",
    },
    {
        "id": 49,
        "name": "Organizador de Bancada",
        "description": "Organizador de bancada para organizar itens na cozinha",
        "price": 100.00,
        "image": "/static/images/gifts/organizador_bancada.jpg",
    },
    {
        "id": 50,
        "name": "Mesa de Apoio",
        "description": "Mesa de apoio para complementar a decoração da casa",
        "price": 280.00,
        "image": "/static/images/gifts/mesa_apoio.jpg",
    },
    {
        "id": 51,
        "name": "Espelho Decorativo",
        "description": "Espelho decorativo para complementar a decoração da casa",
        "price": 450.00,
        "image": "/static/images/gifts/espelho_decorativo.jpg",
    },
    {
        "id": 52,
        "name": "Porta Retratos",
        "description": "Porta retratos para complementar a decoração da casa",
        "price": 70.00,
        "image": "/static/images/gifts/porta_retratos.jpg",
    },
    {
        "id": 53,
        "name": "Difusor de Ambiente",
        "description": "Difusor de ambiente para perfumdar o ambiente",
        "price": 120.00,
        "image": "/static/images/gifts/difusor_ambiente.jpg",
    },
    {
        "id": 54,
        "name": "Filtro de Água",
        "description": "Filtro de água para melhorar a qualidade da água da casa",
        "price": 450.00,
        "image": "/static/images/gifts/filtro_agua.jpg",
    }
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
