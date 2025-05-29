# Importa bibliotecas padrão e externas necessárias
import os  # Para acessar variáveis de ambiente do sistema
import requests  # Para fazer requisições HTTP
from fastapi import FastAPI, Query  # Para criar a API e definir parâmetros de consulta
from pydantic import BaseModel  # Para definir modelos de dados
from dotenv import load_dotenv  # Para carregar variáveis de ambiente de um arquivo .env

# Carrega variáveis de ambiente do arquivo "api.env"
load_dotenv("api.env")

# Lê as variáveis de ambiente que contêm as credenciais do Spotify
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Cria uma instância do FastAPI com um título personalizado
app = FastAPI(title="API Spotify - Buscar Playlists")

# Define o modelo da resposta para a rota de playlists
class Playlist(BaseModel):
    nome: str  # Nome da playlist
    url: str   # URL da playlist no Spotify
    dono: str  # Nome do usuário que criou a playlist

# Função que obtém o token de acesso à API do Spotify
def get_access_token():
    auth_url = 'https://accounts.spotify.com/api/token'  # URL de autenticação do Spotify

    # Autenticação via client credentials
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {
        'grant_type': 'client_credentials',
    }

    # Envia a requisição POST para obter o token
    response = requests.post(auth_url, auth=auth, data=data, timeout=10)
    response.raise_for_status()  # Levanta exceção se a resposta for erro

    # Retorna apenas o token de acesso
    return response.json()['access_token']

# Rota principal da API que busca playlists a partir de uma query
@app.get("/playlists", response_model=list[Playlist])
def buscar_playlists(query: str = Query(..., description="Nome da playlist")):
    # Obtém o token de acesso válido
    access_token = get_access_token()
    
    # Define os headers com o token Bearer
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Define a URL e os parâmetros da requisição de busca
    url = 'https://api.spotify.com/v1/search'
    params = {
        'q': query,          # Termo de busca informado pelo usuário
        'type': 'playlist',  # Tipo de item a buscar (playlist)
        'limit': 5           # Limita o resultado a 5 playlists
    }

    # Envia a requisição GET para buscar as playlists
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()  # Levanta exceção em caso de erro HTTP

    # Converte a resposta JSON para um dicionário Python
    data = response.json()

    # Debug: mostra no terminal as playlists retornadas pela API
    print("Debug playlists data:", data.get('playlists', {}).get('items'))

    # Lista que armazenará os objetos Playlist válidos
    playlists = []
    items = data.get('playlists', {}).get('items', [])
    
    for item in items:
        if not item:
            continue  # Ignora entradas nulas

        # Valida se todas as chaves necessárias existem no item
        if ('name' in item and 
            'external_urls' in item and 
            'spotify' in item['external_urls'] and
            'owner' in item and
            'display_name' in item['owner']):

            # Cria um objeto Playlist com os dados válidos e adiciona à lista
            playlists.append(Playlist(
                nome=item['name'],
                url=item['external_urls']['spotify'],
                dono=item['owner']['display_name']
            ))
        else:
            # Mostra no terminal itens que não foram processados
            print("Item incompleto ignorado:", item)

    # Retorna a lista de playlists para o cliente
    return playlists

# Rota simples de teste, exibida ao acessar o root da API
@app.get("/")
def root():
    return {"mensagem": "API para buscar playlists do Spotify"}


