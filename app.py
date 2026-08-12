import json
import math
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Estaciones Policiales Cercanas", page_icon="🚓", layout="centered")

# ---------- Cargar datos ----------
with open("estaciones.json", "r", encoding="utf-8") as f:
    ESTACIONES = json.load(f)


# ---------- Fórmula de Haversine ----------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # radio de la Tierra en km
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def buscar_estaciones_cercanas(lat, lon, limite=3):
    resultados = []
    for est in ESTACIONES:
        distancia = haversine(lat, lon, est["lat"], est["lon"])
        resultados.append({
            "nombre": est["nombre"],
            "lat": est["lat"],
            "lon": est["lon"],
            "distancia_km": round(distancia, 2)
        })
    resultados.sort(key=lambda x: x["distancia_km"])
    return resultados[:limite]


# ---------- Interfaz ----------
st.title("🚓 Estaciones Policiales Más Cercanas")
st.write("Servicio en la nube que, dadas tus coordenadas, encuentra las estaciones policiales más cercanas.")

with st.form("form_busqueda"):
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitud", value=14.0818, format="%.6f")
    with col2:
        lon = st.number_input("Longitud", value=-87.1921, format="%.6f")

    limite = st.number_input("Cantidad de estaciones a mostrar", min_value=1, max_value=5, value=3)
    buscar = st.form_submit_button("Buscar")

if buscar:
    resultados = buscar_estaciones_cercanas(lat, lon, limite)

    st.subheader("📍 Resultados")
    for i, r in enumerate(resultados, start=1):
        st.markdown(f"**{i}. {r['nombre']}** — {r['distancia_km']} km")

    # Mapa
    df_mapa = pd.DataFrame(resultados)
    df_mapa = pd.concat([
        df_mapa,
        pd.DataFrame([{"nombre": "Tu ubicación", "lat": lat, "lon": lon, "distancia_km": 0}])
    ], ignore_index=True)
    st.map(df_mapa[["lat", "lon"]])

    with st.expander("Ver datos en formato tabla"):
        st.dataframe(df_mapa)

st.divider()
st.caption("Proyecto de clase — Cloud Computing. Estaciones cargadas desde estaciones.json.")
