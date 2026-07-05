"""Rotas do painel administrativo de gerenciamento de convidados RSVP."""

import csv
import io

from fastapi import APIRouter, File, Form, Request, UploadFile
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
async def admin_add_invite(request: Request, name: str = Form(...), max_guests: int = Form(...), phone: str = Form("")):
    success, msg_or_id = database.add_group(name, max_guests, phone or None)
    response = RedirectResponse(url="/admin", status_code=303)
    response.headers["HX-Redirect"] = "/admin"
    return response


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
            headers = [str(c.value).lower().strip() if c.value else "" for c in next(ws.iter_rows(min_row=1, max_row=1))]
            for row in ws.iter_rows(min_row=2, values_only=True):
                def col(keys):
                    for k in keys:
                        if k in headers:
                            v = row[headers.index(k)]
                            return str(v).strip() if v is not None else ""
                    return ""
                name = col(["nome", "name"])
                max_guests_raw = col(["convidados", "max_guests", "vagas"]) or "1"
                phone = col(["telefone", "phone"])
                if name:
                    rows.append({"name": name, "max_guests": int(max_guests_raw or 1), "phone": phone})
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
