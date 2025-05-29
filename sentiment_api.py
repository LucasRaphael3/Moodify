import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Dict

# Carrega variáveis de ambiente
load_dotenv("api.env")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

app = FastAPI(title="API Spotify - Playlists por Sentimento")


class Playlist(BaseModel):
    nome: str
    url: str
    dono: str


def get_access_token():
    """Obtém o token de acesso para autenticação na API do Spotify"""
    auth_url = 'https://accounts.spotify.com/api/token'
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {'grant_type': 'client_credentials'}

    response = requests.post(auth_url, auth=auth, data=data, timeout=10)
    response.raise_for_status()
    return response.json()['access_token']


def buscar_playlists_por_mood(mood: str, access_token: str) -> List[Playlist]:
    """Busca playlists relacionadas a um determinado sentimento (mood)"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    url = 'https://api.spotify.com/v1/search'
    params = {
        'q': mood,
        'type': 'playlist',
        'limit': 3  # limita a 3 playlists por sentimento
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    playlists = []
    items = data.get('playlists', {}).get('items', [])
    for item in items:
        if item and 'name' in item and 'external_urls' in item and 'spotify' in item['external_urls']:
            playlists.append(Playlist(
                nome=item['name'],
                url=item['external_urls']['spotify'],
                dono=item['owner']['display_name']
            ))

    return playlists


@app.get("/moods-playlists", response_model=Dict[str, List[Playlist]])
def playlists_por_sentimentos():
    """Endpoint que retorna playlists para cada sentimento da lista"""
    moods = ["happy songs", "sad songs", "motivated mix", "relaxed mix", "romantic mix"]

    access_token = get_access_token()
    resultado = {}

    for mood in moods:
        try:
            resultado[mood] = buscar_playlists_por_mood(mood, access_token)
        except Exception as e:
            resultado[mood] = []
            print(f"Erro ao buscar playlists para o sentimento '{mood}': {e}")

    return resultado

