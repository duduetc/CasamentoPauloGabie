"""Rotas do painel administrativo de gerenciamento de convidados RSVP."""

import csv
import io
import os
import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from app import database

security = HTTPBasic()

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "casamento2026")


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Acesso negado.",
            headers={"WWW-Authenticate": "Basic"},
        )

router = APIRouter(dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="app/templates")


def _redirect(url: str):
    """Redireciona de forma compatível com HTMX e navegação normal."""
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = url
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, q: str = None):
    from app.routes.gifts import GIFTS
    stats = database.get_stats()
    groups = database.get_all_groups(search_query=q)
    totals = database.get_all_contributions_totals()
    gift_stats = [
        {"name": g["name"], "price": g["price"], "contributed": totals.get(g["id"], 0.0)}
        for g in GIFTS
    ]
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "stats": stats,
            "gift_stats": gift_stats,
            "total_arrecadado": sum(totals.values()),
            "groups": groups,
            "search_query": q or "",
        }
    )


@router.post("/admin/convite", response_class=HTMLResponse)
async def admin_add_invite(request: Request, name: str = Form(...), max_guests: int = Form(...), phone: str = Form("")):
    success, msg_or_id = database.add_group(name, max_guests, phone or None)
    return _redirect("/admin")


@router.post("/admin/importar", response_class=HTMLResponse)
async def admin_import(request: Request, file: UploadFile = File(...)):
    filename = file.filename.lower()
    rows = []
    error = None

    try:
        if filename.endswith(".csv"):
            content = (await file.read()).decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            for r in reader:
                # aceita cabeçalhos em português ou inglês
                name = r.get("nome") or r.get("name") or r.get("Nome") or r.get("Name") or ""
                max_guests_raw = r.get("convidados") or r.get("max_guests") or r.get("Convidados") or r.get("vagas") or r.get("Vagas") or "1"
                phone = r.get("telefone") or r.get("phone") or r.get("Telefone") or r.get("Phone") or ""
                if name.strip():
                    rows.append({"name": name.strip(), "max_guests": int(str(max_guests_raw).strip() or 1), "phone": phone.strip()})

        elif filename.endswith(".xlsx"):
            import openpyxl
            content = await file.read()
            wb = openpyxl.load_workbook(io.BytesIO(content))
            ws = wb.active

            # col A = Quant., col B = Nome Subscrito, col C = Nome do convidado, col D = Celular
            # Linhas principais: col A é número e col B tem texto
            # Sub-linhas: col A e B vazias, col C tem nome do acompanhante
            current = None
            for row in ws.iter_rows(min_row=4, values_only=True):
                quant     = row[0] if len(row) > 0 else None
                nome      = row[1] if len(row) > 1 else None
                guest_col = row[2] if len(row) > 2 else None
                phone_val = row[3] if len(row) > 3 else None

                if isinstance(quant, (int, float)) and nome:
                    # linha principal do convite
                    current = {
                        "name": str(nome).strip(),
                        "max_guests": int(quant),
                        "phone": str(phone_val).strip() if phone_val else "",
                        "guest_names": [str(guest_col).strip()] if guest_col else [],
                    }
                    rows.append(current)
                elif current and guest_col and not quant and not nome:
                    # sub-linha de acompanhante
                    guest_name = str(guest_col).strip()
                    if guest_name:
                        current["guest_names"].append(guest_name)
        else:
            error = "Formato não suportado. Envie um arquivo .csv ou .xlsx."

    except Exception as e:
        error = f"Erro ao processar arquivo: {e}"

    if error:
        return templates.TemplateResponse("pages/admin.html", {
            "request": request,
            "stats": database.get_stats(),
            "groups": database.get_all_groups(),
            "search_query": "",
            "import_error": error,
        })

    inserted, duplicates = database.add_groups_bulk(rows)
    response = RedirectResponse(url=f"/admin?imported={inserted}&duplicates={duplicates}", status_code=303)
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
async def admin_edit_invite(request: Request, group_id: int, name: str = Form(...), max_guests: int = Form(...), phone: str = Form("")):
    success, msg = database.update_group(group_id, name, max_guests, phone or None)
    if not success:
        group = database.get_group_by_id(group_id)
        return templates.TemplateResponse(
            "partials/admin_edit_modal.html",
            {"request": request, "group": group, "error": msg}
        )

    return _redirect("/admin")


@router.post("/admin/convite/{group_id}/resetar", response_class=HTMLResponse)
async def admin_reset_invite(request: Request, group_id: int):
    database.reset_group_rsvp(group_id)
    return _redirect("/admin")


@router.post("/admin/convite/{group_id}/deletar", response_class=HTMLResponse)
async def admin_delete_invite(request: Request, group_id: int):
    database.delete_group(group_id)
    return _redirect("/admin")


@router.post("/admin/contribuicoes/{gift_id}/remover", response_class=HTMLResponse)
async def admin_remove_contribution(request: Request, gift_id: int, amount: float = Form(...)):
    from app.routes.gifts import GIFTS

    gift = next((g for g in GIFTS if g["id"] == gift_id), None)
    gift_name = gift["name"] if gift else ""
    removed = database.remove_contribution(gift_id, amount, gift_name=gift_name)

    if removed:
        return RedirectResponse(url="/admin?removed=1", status_code=303)
    return RedirectResponse(url="/admin?removal_error=1", status_code=303)
