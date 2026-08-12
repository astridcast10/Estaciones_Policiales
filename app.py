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

    ICONO_ESTACION = {
        "url": "data:image/png;base64,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",
        "width": 128, "height": 128, "anchorY": 64,
    }
    ICONO_USUARIO = {
        "url": "data:image/png;base64,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",
        "width": 128, "height": 168, "anchorY": 168,
    }

    df_estaciones["icon"] = [ICONO_ESTACION] * len(df_estaciones)
    df_usuario["icon"] = [ICONO_USUARIO] * len(df_usuario)

    capa_estaciones = pdk.Layer(
        "IconLayer",
        data=df_estaciones,
        get_icon="icon",
        get_position="[lon, lat]",
        get_size=4,
        size_scale=13,
        pickable=True,
    )

    capa_usuario = pdk.Layer(
        "IconLayer",
        data=df_usuario,
        get_icon="icon",
        get_position="[lon, lat]",
        get_size=4,
        size_scale=15,
        pickable=True,
    )

    vista = pdk.ViewState(latitude=lat, longitude=lon, zoom=12)

    st.pydeck_chart(pdk.Deck(
        layers=[capa_estaciones, capa_usuario],
        initial_view_state=vista,
        tooltip={"text": "{nombre}"}
    ))
    st.caption("🛡️ Estaciones policiales &nbsp;&nbsp; 📍 Tu ubicación")

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
