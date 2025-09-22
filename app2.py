import os
import pandas as pd
import streamlit as st
import tweepy
from datetime import datetime, timezone, timedelta
from openai import OpenAI
from dotenv import load_dotenv

st.title("🚀 Probando mi app de Streamlit")
st.write("Si ves este mensaje, Streamlit está funcionando correctamente ✅")

# -------------------------
# 🔑 Cargar credenciales desde .env
# -------------------------
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar clientes
twitter_client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)
gpt_client = OpenAI(api_key=OPENAI_API_KEY)

# Función para buscar tweets
def buscar_tweets(query, fecha_inicio, max_tweets=20):
    ahora = datetime.now(timezone.utc)
    end_time = ahora - timedelta(seconds=10)  # 10 segundos antes de ahora
    end_time_iso = end_time.isoformat(timespec='seconds').replace('+00:00', 'Z')

    tweets = twitter_client.search_recent_tweets(
        query=query,
        start_time=f"{fecha_inicio}T00:00:00Z",
        end_time=end_time_iso,
        max_results=min(max_tweets, 100),
        tweet_fields=["id", "text", "author_id", "created_at"]
    )

    data = []
    if tweets.data:
        for tweet in tweets.data:
            data.append({
                "id": tweet.id,
                "texto": tweet.text,
                "autor": tweet.author_id,
                "fecha": tweet.created_at.replace(tzinfo=None)
            })

    return pd.DataFrame(data)

# Función para análisis de sentimiento con GPT
def analizar_sentimiento(texto):
    prompt = f"Clasifica este texto de Twitter en positivo, negativo o neutro(Solo una palabra como respuesta):\n\nTexto: {texto}\n\n"
    try:
        response = gpt_client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        sentimiento = response.output[0].content[0].text.strip()
        return sentimiento
    except Exception as e:
        return "Error"

# --- Interfaz en Streamlit ---
st.title("📊 Buscador de Tweets con Análisis de Sentimiento")

palabra = st.text_input("🔎 Ingresa la palabra clave a buscar")
inicio = st.date_input("📅 Fecha inicio")
fin = st.date_input("📅 Fecha fin")

if st.button("Buscar y Analizar"):
    if palabra and inicio and fin:
        with st.spinner("Buscando tweets..."):
            df = buscar_tweets(palabra, str(inicio), max_tweets=20)

        if not df.empty:
            st.success(f"Se encontraron {len(df)} tweets. Analizando...")

            # Analizar sentimientos
            df["sentimiento"] = df["texto"].apply(analizar_sentimiento)

            # Mostrar tabla
            st.dataframe(df)

            # Descargar Excel
            nombre_archivo = f"tweets_{palabra}_{inicio}_a_{fin}.xlsx"
            df.to_excel(nombre_archivo, index=False)

            with open(nombre_archivo, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=f,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No se encontraron tweets con esos criterios.")
    else:
        st.error("Por favor ingresa palabra clave y fechas.")
