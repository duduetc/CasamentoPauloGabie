"""Bootstrap da aplicação FastAPI do site de casamento."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes.admin import router as admin_router
from app.routes.gifts import router as gifts_router
from app.routes.public import router as public_router
from app.routes.rsvp import router as rsvp_router

# Inicializa o banco de dados
init_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(public_router)
app.include_router(gifts_router)
app.include_router(rsvp_router)
app.include_router(admin_router)

