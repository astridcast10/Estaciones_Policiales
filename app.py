import json
import math
import streamlit as st
import pandas as pd
import pydeck as pdk
from streamlit_js_eval import get_geolocation

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


def mostrar_resultados(lat, lon, limite):
    resultados = buscar_estaciones_cercanas(lat, lon, limite)

    st.subheader("📍 Resultados")
    for i, r in enumerate(resultados, start=1):
        st.markdown(f"**{i}. {r['nombre']}** — {r['distancia_km']} km")

    df_estaciones = pd.DataFrame(resultados)
    df_usuario = pd.DataFrame([{"nombre": "Tu ubicación", "lat": lat, "lon": lon}])

    capa_estaciones = pdk.Layer(
        "ScatterplotLayer",
        data=df_estaciones,
        get_position="[lon, lat]",
        get_fill_color="[220, 30, 30, 200]",  # rojo
        get_radius=120,
        pickable=True,
    )

    capa_usuario = pdk.Layer(
        "ScatterplotLayer",
        data=df_usuario,
        get_position="[lon, lat]",
        get_fill_color="[30, 90, 220, 220]",  # azul
        get_radius=180,
        pickable=True,
    )

    vista = pdk.ViewState(latitude=lat, longitude=lon, zoom=12)

    st.pydeck_chart(pdk.Deck(
        layers=[capa_estaciones, capa_usuario],
        initial_view_state=vista,
        tooltip={"text": "{nombre}"}
    ))
    st.caption("🔴 Estaciones policiales &nbsp;&nbsp; 🔵 Tu ubicación")

    with st.expander("Ver datos en formato tabla"):
        st.dataframe(pd.concat([df_estaciones, df_usuario], ignore_index=True))


# ---------- Interfaz ----------
st.title("🚓 Estaciones Policiales Más Cercanas")
st.write("Servicio en la nube que encuentra las estaciones policiales más cercanas según tu ubicación.")

limite = st.number_input("Cantidad de estaciones a mostrar", min_value=1, max_value=5, value=3)

tab_gps, tab_manual = st.tabs(["📡 Usar mi ubicación", "✍️ Escribir coordenadas"])

with tab_gps:
    st.write("Presiona el botón y acepta el permiso de ubicación que te pida el navegador.")

    if st.button("Usar mi ubicación actual"):
        st.session_state["quiere_gps"] = True

    if st.session_state.get("quiere_gps"):
        # Este componente necesita 1-2 reruns automáticos para resolver el permiso
        # del navegador, así que la bandera de arriba debe seguir activa mientras tanto.
        ubicacion = get_geolocation()
        if ubicacion is not None:
            lat = ubicacion["coords"]["latitude"]
            lon = ubicacion["coords"]["longitude"]
            st.success(f"Ubicación detectada: {lat:.6f}, {lon:.6f}")
            mostrar_resultados(lat, lon, limite)
        else:
            st.info("Obteniendo tu ubicación... si no cambia en unos segundos, revisa el permiso de ubicación en el candado del navegador y vuelve a presionar el botón.")

with tab_manual:
    with st.form("form_manual"):
        col1, col2 = st.columns(2)
        with col1:
            lat_m = st.number_input("Latitud", value=14.0818, format="%.6f")
        with col2:
            lon_m = st.number_input("Longitud", value=-87.1921, format="%.6f")
        buscar_manual = st.form_submit_button("Buscar")

    if buscar_manual:
        mostrar_resultados(lat_m, lon_m, limite)

st.divider()
st.caption("Proyecto de clase — Cloud Computing. Estaciones cargadas desde estaciones.json.")
