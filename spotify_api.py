import os
import requests
from fastapi import FastAPI, Query
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv("api.env")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

app = FastAPI(title="API Spotify - Buscar Playlists")

class Playlist(BaseModel):
    nome: str
    url: str
    dono: str

def get_access_token():
    auth_url = 'https://accounts.spotify.com/api/token'
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post(auth_url, auth=auth, data=data, timeout=10)
    response.raise_for_status()
    return response.json()['access_token']

@app.get("/playlists", response_model=list[Playlist])
def buscar_playlists(query: str = Query(..., description="Nome da playlist")):
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    url = 'https://api.spotify.com/v1/search'
    params = {
        'q': query,
        'type': 'playlist',
        'limit': 5
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    # Debug: imprima para analisar o conteúdo
    print("Debug playlists data:", data.get('playlists', {}).get('items'))

    playlists = []
    items = data.get('playlists', {}).get('items', [])
    for item in items:
        if not item:
            # pula item None
            continue
        # Valida presença das chaves importantes
        if ('name' in item and 
            'external_urls' in item and 
            'spotify' in item['external_urls'] and
            'owner' in item and
            'display_name' in item['owner']):

            playlists.append(Playlist(
                nome=item['name'],
                url=item['external_urls']['spotify'],
                dono=item['owner']['display_name']
            ))
        else:
            print("Item incompleto ignorado:", item)

    return playlists


@app.get("/")
def root():
    return {"mensagem": "API para buscar playlists do Spotify"}

