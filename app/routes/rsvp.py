"""Rotas de confirmação RSVP por nome de convite e acompanhantes."""

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app import database

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/confirmacao", response_class=HTMLResponse)
async def rsvp_page(request: Request):
    return templates.TemplateResponse("pages/rsvp.html", {"request": request})


@router.post("/confirmacao/buscar", response_class=HTMLResponse)
async def rsvp_search(request: Request, name: str = Form("")):
    name_str = name.strip()
    if not name_str:
        return HTMLResponse(
            "<div class='bg-red-50 text-red-700 p-4 rounded-sm font-body text-center border border-red-200'>"
            "Por favor, insira o seu nome para pesquisar."
            "</div>"
        )

    results = database.search_groups(name_str)
    return templates.TemplateResponse(
        "partials/rsvp_form.html",
        {
            "request": request,
            "results": results,
            "search_query": name_str,
            "step": "search_results",
        },
    )


@router.get("/confirmacao/{group_id}/form", response_class=HTMLResponse)
async def rsvp_get_form(request: Request, group_id: int):
    group = database.get_group_by_id(group_id)
    if not group:
        return HTMLResponse(
            "<div class='bg-red-50 text-red-700 p-4 rounded-sm font-body text-center border border-red-200'>"
            "Convite não encontrado."
            "</div>",
            status_code=404,
        )

    return templates.TemplateResponse(
        "partials/rsvp_form.html",
        {"request": request, "group": group, "step": "confirm_form"},
    )


@router.post("/confirmacao/{group_id}/confirmar", response_class=HTMLResponse)
async def rsvp_confirm(request: Request, group_id: int):
    group = database.get_group_by_id(group_id)
    if not group:
        return HTMLResponse(
            "<div class='bg-red-50 text-red-700 p-4 rounded-sm font-body text-center border border-red-200'>"
            "Convite não encontrado."
            "</div>",
            status_code=404,
        )

    form_data = await request.form()
    main_name = form_data.get("main_name", "").strip()
    attending_main = form_data.get("attending_main")  # "on" se marcado, None caso contrário

    confirmed_names = []
    if attending_main == "on" and main_name:
        confirmed_names.append(main_name)

    # Extrai acompanhantes dinamicamente
    companion_names = []
    for key, val in form_data.items():
        if key.startswith("companion_name_") and val and val.strip():
            companion_names.append(val.strip())

    # Enforça o limite máximo de acompanhantes
    max_companions = max(0, group["max_guests"] - 1)
    companion_names = companion_names[:max_companions]

    confirmed_names.extend(companion_names)
    confirmed_count = len(confirmed_names)

    if confirmed_count == 0:
        return HTMLResponse(
            "<div class='bg-red-50 text-red-700 p-4 rounded-sm font-body text-center border border-red-200 mb-4'>"
            "Você deve selecionar ao menos um participante para confirmar. Se ninguém puder comparecer, use a opção de declinar convite."
            "</div>"
        )

    database.update_group_rsvp(
        group_id=group_id,
        status="confirmed",
        confirmed_count=confirmed_count,
        confirmed_names=confirmed_names,
        declined_reason=None,
    )

    updated_group = database.get_group_by_id(group_id)
    return templates.TemplateResponse(
        "partials/rsvp_success.html",
        {"request": request, "group": updated_group, "confirmed": True},
    )


@router.post("/confirmacao/{group_id}/declinar", response_class=HTMLResponse)
async def rsvp_decline(request: Request, group_id: int):
    group = database.get_group_by_id(group_id)
    if not group:
        return HTMLResponse(
            "<div class='bg-red-50 text-red-700 p-4 rounded-sm font-body text-center border border-red-200'>"
            "Convite não encontrado."
            "</div>",
            status_code=404,
        )

    form_data = await request.form()
    declined_reason = form_data.get("declined_reason", "").strip()

    database.update_group_rsvp(
        group_id=group_id,
        status="declined",
        confirmed_count=0,
        confirmed_names=[],
        declined_reason=declined_reason if declined_reason else None,
    )

    updated_group = database.get_group_by_id(group_id)
    return templates.TemplateResponse(
        "partials/rsvp_success.html",
        {"request": request, "group": updated_group, "confirmed": False},
    )
