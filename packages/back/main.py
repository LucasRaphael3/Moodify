from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from passlib.hash import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import spotify_api 
import traceback

# ----- CONFIG -----
DATABASE_URL = "sqlite:///./usuarios.db"
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ----- DB SETUP -----
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ----- MODELS -----
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# ----- SCHEMAS -----
class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# ----- AUTH UTILS -----
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# ----- FASTAPI APP -----
app = FastAPI(title="Sistema de Login/Cadastro com JWT")

# --- CONFIGURAÇÃO DO CORS ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO PARA SERVIR ARQUIVOS HTML ---
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/cadastro", response_class=HTMLResponse)
async def get_cadastro_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.get("/telaescolhamood", response_class=HTMLResponse)
async def get_escolhamood_page(request: Request):
    return templates.TemplateResponse("telaescolhamood.html", {"request": request})

@app.get("/telaplaylist", response_class=HTMLResponse)
async def get_telaplaylist_page(request: Request):
    return templates.TemplateResponse("telaplaylist.html", {"request": request})


# ----- API ENDPOINTS -----

@app.post("/register", response_model=dict)
def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="Email já registrado")

    senha_hash = bcrypt.hash(usuario.senha)
    novo_usuario = Usuario(nome=usuario.nome, email=usuario.email, senha_hash=senha_hash)
    db.add(novo_usuario)
    db.commit()
    return {"mensagem": "Usuário registrado com sucesso"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # O form_data espera os campos 'username' e 'password'
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not usuario or not bcrypt.verify(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROTA PARA BUSCAR PLAYLISTS ---
@app.get("/playlist/{mood}")
async def get_playlist_by_mood(mood: str):
    mood_to_query_map = {
        "happy": "good vibes",
        "sad": "melancolic songs",
        "party": "Nostalgic",
        "relax": "Relaxing Music"
    }
    search_query = mood_to_query_map.get(mood.lower(), "Pop Up")

    try:
        spotify_data = spotify_api.search_spotify_playlist(search_query, limit=4)

        if spotify_data is None:
            raise HTTPException(status_code=502, detail="Falha na comunicação com a API do Spotify.")

        items = spotify_data.get('playlists', {}).get('items', [])
        
        if not items:
            raise HTTPException(status_code=404, detail=f"Nenhuma playlist encontrada para '{search_query}'.")

        # 2. Criamos uma lista para armazenar os resultados formatados
        results_list = []
        
        # 3. Usamos um loop para processar cada playlist encontrada
        for playlist in items:
            # Garantimos que o item não é nulo antes de processar
            if playlist:
                image_url = playlist['images'][0]['url'] if playlist.get('images') else None
                external_url = playlist['external_urls']['spotify'] if playlist.get('external_urls') else None
                
                results_list.append({
                    "name": playlist.get("name"),
                    "external_url": external_url,
                    "image_url": image_url
                })
        
        # 4. Retornamos um dicionário contendo a lista de playlists
        return {"playlists": results_list}

@app.get("/me")
def read_users_me(current_user: Usuario = Depends(get_current_user)):
    # Esta é uma rota protegida. Só pode ser acessada com um token válido.
    return {"nome": current_user.nome, "email": current_user.email}

@app.get("/", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    """Serve a página de login como a página inicial."""
    return templates.TemplateResponse("login.html", {"request": request})
