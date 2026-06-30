"""Rotas do painel administrativo de gerenciamento de convidados RSVP."""

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app import database

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, q: str = None):
    stats = database.get_stats()
    groups = database.get_all_groups(search_query=q)
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "stats": stats,
            "groups": groups,
            "search_query": q or "",
        }
    )


@router.post("/admin/convite", response_class=HTMLResponse)
async def admin_add_invite(request: Request, name: str = Form(...), max_guests: int = Form(...)):
    success, msg_or_id = database.add_group(name, max_guests)
    response = RedirectResponse(url="/admin", status_code=303)
    response.headers["HX-Redirect"] = "/admin"
    return response


@router.get("/admin/convite/{group_id}/editar", response_class=HTMLResponse)
async def admin_edit_form(request: Request, group_id: int):
    group = database.get_group_by_id(group_id)
    if not group:
        return HTMLResponse("<p class='p-4 text-red-500 font-body'>Convite não encontrado.</p>", status_code=404)

    return templates.TemplateResponse(
        "partials/admin_edit_modal.html",
        {"request": request, "group": group}
    )


@router.post("/admin/convite/{group_id}/editar", response_class=HTMLResponse)
async def admin_edit_invite(request: Request, group_id: int, name: str = Form(...), max_guests: int = Form(...)):
    success, msg = database.update_group(group_id, name, max_guests)
    if not success:
        group = database.get_group_by_id(group_id)
        return templates.TemplateResponse(
            "partials/admin_edit_modal.html",
            {"request": request, "group": group, "error": msg}
        )

    response = RedirectResponse(url="/admin", status_code=303)
    response.headers["HX-Redirect"] = "/admin"
    return response


@router.post("/admin/convite/{group_id}/resetar", response_class=HTMLResponse)
async def admin_reset_invite(request: Request, group_id: int):
    database.reset_group_rsvp(group_id)
    response = RedirectResponse(url="/admin", status_code=303)
    response.headers["HX-Redirect"] = "/admin"
    return response


@router.post("/admin/convite/{group_id}/deletar", response_class=HTMLResponse)
async def admin_delete_invite(request: Request, group_id: int):
    database.delete_group(group_id)
    response = RedirectResponse(url="/admin", status_code=303)
    response.headers["HX-Redirect"] = "/admin"
    return response
