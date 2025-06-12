import os
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo "api.env"
load_dotenv(dotenv_path="api.env")

# Lê as credenciais do Spotify do seu arquivo .env
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_access_token():
    """Obtém um token de acesso à API do Spotify."""
    
     # --- INÍCIO DO DEBUG DE AUTENTICAÇÃO ---
    print("\n--- DEBUG DE AUTENTICAÇÃO ---")
    print(f"ID do Cliente lido do .env: '{SPOTIFY_CLIENT_ID}'")
    print(f"Segredo do Cliente lido do .env: '{SPOTIFY_CLIENT_SECRET}'")
    print("-----------------------------\n")

    # Verificação para garantir que as variáveis foram carregadas
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("ERRO CRÍTICO: CLIENT_ID ou CLIENT_SECRET não foram carregados. Verifique se o nome e o local do arquivo api.env estão corretos.")
        return None
    # --- FIM DO DEBUG ---
    
    auth_url = 'https://accounts.spotify.com/api/token'

    try:
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        }, timeout=10)
        
        # Levanta uma exceção se a resposta indicar um erro HTTP
        auth_response.raise_for_status()
        auth_data = auth_response.json()
        return auth_data['access_token']
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter token de acesso: {e}")
        return None

def search_spotify_playlist(query: str, limit: int = 1):
    """
    Busca playlists no Spotify com base em uma query e retorna os dados da API.
    """
    access_token = get_access_token()
    if not access_token:
        print("Não foi possível obter o token de acesso. A busca será cancelada.")
        return None

    # URL DE BUSCA CORRETA DA API DO SPOTIFY
    search_url = 'https://api.spotify.com/v1/search'
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': query,
        'type': 'playlist',
        'limit': limit
    }

    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar playlist no Spotify: {e}")
        return None
    
    
