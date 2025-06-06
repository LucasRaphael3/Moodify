from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from packages.back.database import SessionLocal, engine
from packages.back import models, crud

import os

# Cria as tabelas no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Caminhos para templates e arquivos estáticos
base_dir = os.path.dirname(os.path.abspath(__file__))
front_dir = os.path.abspath(os.path.join(base_dir, "..", "front"))

app.mount("/static", StaticFiles(directory=front_dir), name="static")
templates = Jinja2Templates(directory=front_dir)

# Dependência do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ROTAS ----------

# Tela de login
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("Tela inicial.html", {"request": request})


# Tela de cadastro
@app.get("/cadastro", response_class=HTMLResponse)
def cadastro_page(request: Request):
    return templates.TemplateResponse("Tela cadastro.html", {"request": request})


# Processa o formulário de cadastro
@app.post("/cadastro")
def processar_cadastro(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    user_existente = crud.get_user_by_email(db, email=email)
    if user_existente:
        return RedirectResponse(url="/cadastro", status_code=302)

    crud.create_user(db, nome=nome, email=email, senha=senha)
    return RedirectResponse(url="/", status_code=302)


# Processa o login (se quiser implementar depois)
@app.post("/login")
def processar_login(
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=email)
    if user and user.senha == senha:
        # Aqui você pode redirecionar para a home do sistema
        return RedirectResponse(url="/", status_code=302)
    return RedirectResponse(url="/", status_code=302)
