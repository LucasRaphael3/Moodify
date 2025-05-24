import fastapi
from pydantic import BaseModel
from textblob import TextBlob

app = fastapi.FastAPI(title="API de Análise de Sentimentos")

class TextoEntrada(BaseModel):
    texto: str

class SentimentoSaida(BaseModel):
    polaridade: float
    sentimento: str

@app.post("/sentimento", response_model=SentimentoSaida)
def analisar_sentimento(entrada: TextoEntrada):
    blob = TextBlob(entrada.texto)
    polaridade = blob.sentiment.polarity

    if polaridade > 0:
        sentimento = "positivo"
    elif polaridade < 0:
        sentimento = "negativo"
    else:
        sentimento = "neutro"

    return SentimentoSaida(polaridade=polaridade, sentimento=sentimento)

@app.get("/")
def root():
    return {"mensagem": "API de Análise de Sentimentos está no ar!"}
