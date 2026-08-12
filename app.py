import json
import math
import requests
import streamlit as st
import pandas as pd
import pydeck as pdk
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Estaciones Policiales Cercanas", page_icon="🚓", layout="centered")

# ---------- Estaciones de respaldo (por si OpenStreetMap no responde) ----------
with open("estaciones.json", "r", encoding="utf-8") as f:
    ESTACIONES_RESPALDO = json.load(f)

# ---------- Velocidades promedio para estimar tiempo de llegada ----------
VELOCIDADES_KMH = {
    "🚶 A pie": 5,
    "🚴 Bicicleta": 15,
    "🚗 Carro": 35,
    "🚌 Bus": 18,
}


# ---------- Fórmula de Haversine ----------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # radio de la Tierra en km
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def formatear_minutos(minutos):
    if minutos < 60:
        return f"{minutos:.0f} min"
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas} h {mins} min"


def estimar_tiempos(distancia_km):
    """Estimado a partir de distancia en línea recta / velocidad promedio de cada medio.
    No es una ruta real (no considera calles, tráfico, rutas de bus), es una aproximación."""
    return {modo: distancia_km / vel * 60 for modo, vel in VELOCIDADES_KMH.items()}


# ---------- Buscar estaciones policiales reales en OpenStreetMap ----------
@st.cache_data(show_spinner=False, ttl=3600)
def obtener_estaciones_osm(lat, lon):
    """Busca puestos policiales reales cerca de (lat, lon) usando la API pública
    Overpass de OpenStreetMap, ampliando el radio de búsqueda si hace falta."""
    radios_m = [3000, 6000, 12000, 25000, 50000]
    for radio in radios_m:
        query = f"""
        [out:json][timeout:20];
        (
          node["amenity"="police"](around:{radio},{lat},{lon});
          way["amenity"="police"](around:{radio},{lat},{lon});
          relation["amenity"="police"](around:{radio},{lat},{lon});
        );
        out center;
        """
        try:
            resp = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        estaciones = []
        for el in data.get("elements", []):
            if el["type"] == "node":
                elat, elon = el.get("lat"), el.get("lon")
            else:
                centro = el.get("center", {})
                elat, elon = centro.get("lat"), centro.get("lon")
            if elat is None or elon is None:
                continue
            nombre = el.get("tags", {}).get("name") or "Puesto policial (OpenStreetMap)"
            estaciones.append({"nombre": nombre, "lat": elat, "lon": elon})

        if len(estaciones) >= 3:
            return estaciones, radio

    return [], None


def buscar_estaciones_cercanas(lat, lon, limite=3):
    estaciones_reales, radio_usado = obtener_estaciones_osm(lat, lon)

    if estaciones_reales:
        fuente = "osm"
        catalogo = estaciones_reales
    else:
        fuente = "respaldo"
        catalogo = ESTACIONES_RESPALDO

    resultados = []
    for est in catalogo:
        distancia = haversine(lat, lon, est["lat"], est["lon"])
        resultados.append({
            "nombre": est["nombre"],
            "lat": est["lat"],
            "lon": est["lon"],
            "distancia_km": round(distancia, 2),
        })
    resultados.sort(key=lambda x: x["distancia_km"])
    return resultados[:limite], fuente


def mostrar_resultados(lat, lon, limite):
    with st.spinner("Buscando estaciones policiales reales cerca de tu ubicación..."):
        resultados, fuente = buscar_estaciones_cercanas(lat, lon, limite)

    if fuente == "respaldo":
        st.warning(
            "No se encontraron puestos policiales registrados en OpenStreetMap cerca de tu "
            "ubicación (o el servicio no respondió), así que se muestran estaciones de respaldo "
            "de ejemplo. En una emergencia real, llama al 911."
        )
    else:
        st.caption("Estaciones obtenidas en tiempo real desde OpenStreetMap.")

    st.subheader("📍 Resultados")
    for i, r in enumerate(resultados, start=1):
        tiempos = estimar_tiempos(r["distancia_km"])
        st.markdown(f"**{i}. {r['nombre']}** — {r['distancia_km']} km")
        cols = st.columns(len(tiempos))
        for col, (modo, minutos) in zip(cols, tiempos.items()):
            col.metric(modo, formatear_minutos(minutos))

    st.caption("⏱️ Tiempos estimados según distancia en línea recta y velocidad promedio de cada medio (no son rutas reales de calles ni horarios de bus).")

    df_estaciones = pd.DataFrame(resultados)
    df_usuario = pd.DataFrame([{"nombre": "Tu ubicación", "lat": lat, "lon": lon}])

    ICONO_ESTACION = {
        "url": "data:image/png;base64,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",
        "width": 128, "height": 128, "anchorY": 64,
    }
    ICONO_USUARIO = {
        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACoCAYAAAAbi7hDAAAABmJLR0QA/wD/AP+gvaeTAAABsklEQVR4nO3dwW3CQBBAUYNoIJ2EEnJIA1TgHrhwoIJUAMdcOaVGSCFOh05CDmYtZE/8DsBefv7fTLpqNMc4a4wCq7X24pw7lVJezWx0zpXW2mSMma/72Y96ZlrPn/3JzE7GmMcYY/w3fD/RdlrgD9BaP4YQTlmXPlrgz/HeH0IIp5xnfRfg+Xnv8977Y65zP4ppzo3btm2ap1yvz2yBH9Bau9Va+7KsWXovwHRttXaz3jsFqNZaJWUxaBQghhi7VgFCCB8ppcQoQIoxvqUeMwqQUnpPPWYUIMY4pR4zClCttWvKNXddV0Q4UcolY13XZlmWZlqOwiCEUKy1V+/9WLbtqIN0XVdaa0Nr7cs5V3rvi3lqNsY0QRkVYFVKGZ1zt6VVXf2SbbmU8jf7WjWDFECAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCiCAAggQCvADBAoOtcVUDsIAAAAASUVORK5CYII=",
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
        st.dataframe(pd.concat([df_estaciones.drop(columns="icon"), df_usuario.drop(columns="icon")], ignore_index=True))


# ---------- Interfaz ----------
st.title("🚓 Estaciones Policiales Más Cercanas")
st.write(
    "Servicio en la nube que encuentra las estaciones policiales reales más cercanas a tu "
    "ubicación (usando OpenStreetMap) y estima cuánto tardarías en llegar a pie, en bici, "
    "en carro o en bus."
)

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
st.caption(
    "Proyecto de clase — Cloud Computing. Estaciones en tiempo real vía OpenStreetMap/Overpass; "
    "si no hay datos disponibles cerca, se usa un respaldo de ejemplo (estaciones.json)."
)
