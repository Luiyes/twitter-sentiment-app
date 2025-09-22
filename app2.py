import os
import pandas as pd
import streamlit as st
from pytwitter import Api
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

# --- Título de la app ---
st.title("📊 Buscador de Tweets con Análisis de Sentimiento")

# -------------------------
# 🔑 Cargar credenciales desde .env
# -------------------------
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar clientes
twitter_api = Api(bearer_token=BEARER_TOKEN)
gpt_client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------
# Función para buscar tweets
# -------------------------
def buscar_tweets(query, fecha_inicio, fecha_fin=None, max_tweets=20):
    from datetime import datetime, timezone, timedelta
    ahora = datetime.now(timezone.utc)

    if fecha_fin is None:
        fecha_fin = ahora
    elif isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        fecha_fin = fecha_fin.replace(tzinfo=timezone.utc, hour=23, minute=59, second=0)

    # Ajuste para que end_time nunca sea futuro
    if fecha_fin > ahora - timedelta(seconds=10):
        fecha_fin = ahora - timedelta(seconds=10)

    end_time_iso = fecha_fin.isoformat(timespec='seconds')

    # Llamada a la API
    respuesta = twitter_api.search_tweets(
        query=query,
        start_time=f"{fecha_inicio}T00:00:00Z",
        end_time=end_time_iso,
        max_results=min(max_tweets, 100)
    )

    # Convertir respuesta a DataFrame
    data = []
    if respuesta.data:
        for tweet in respuesta.data:
            data.append({
                "id": tweet.id,
                "texto": tweet.text,
                "autor": tweet.author_id,
                "fecha": tweet.created_at
            })
    return pd.DataFrame(data)

# -------------------------
# Función para análisis de sentimiento con GPT
# -------------------------
def analizar_sentimiento(texto):
    prompt = f"Clasifica este texto de Twitter en positivo, negativo o neutro(solo una palabra en la respuesta):\n\nTexto: {texto}\n\n"
    try:
        response = gpt_client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        sentimiento = response.output[0].content[0].text.strip()
        return sentimiento
    except Exception:
        return "Error"

# --- Interfaz en Streamlit ---
palabra = st.text_input("🔎 Ingresa la palabra clave a buscar")
inicio = st.date_input("📅 Fecha inicio")
fin = st.date_input("📅 Fecha fin")

if st.button("Buscar y Analizar"):
    if palabra and inicio:
        with st.spinner("Buscando tweets..."):
            df = buscar_tweets(palabra, str(inicio), str(fin), max_tweets=20)

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

