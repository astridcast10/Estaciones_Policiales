import json
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="Estaciones Policiales Más Cercanas",
    page_icon="🚓",
    layout="centered",
)

# ---------- Estilos ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #f4f6fb 0%, #eef1f8 100%);
    }
    .banner-policia {
        background: linear-gradient(135deg, #0b1f4d 0%, #16327a 55%, #b91c1c 100%);
        padding: 28px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(11,31,77,0.28);
    }
    .banner-policia h1 {
        color: white !important;
        margin: 0 0 8px 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .banner-policia p {
        margin: 0;
        color: #dbe4ff;
        font-size: 0.97rem;
        line-height: 1.4;
    }
    .stats-fila {
        display: flex;
        gap: 12px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    .stat-chip {
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .seccion-card {
        background: white;
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 3px 14px rgba(20,30,60,0.08);
        margin-bottom: 20px;
        border: 1px solid #eceff5;
    }
    .tarjeta-estacion {
        border: 1px solid #eee0e0;
        border-left: 7px solid #b91c1c;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        background: #fffafa;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .tarjeta-estacion .num {
        display: inline-block;
        background: #b91c1c;
        color: white;
        font-weight: 700;
        border-radius: 50%;
        width: 26px;
        height: 26px;
        text-align: center;
        line-height: 26px;
        margin-right: 8px;
        font-size: 0.9rem;
    }
    .tarjeta-estacion .nombre {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0b1f4d;
    }
    .tarjeta-estacion .distancia {
        display: inline-block;
        background: #16327a;
        color: white;
        border-radius: 999px;
        padding: 3px 13px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 6px;
        float: right;
    }
    .tiempos-fila {
        display: flex;
        gap: 8px;
        margin-top: 10px;
        flex-wrap: wrap;
    }
    .tiempo-pill {
        background: #eef1fb;
        border: 1px solid #ccd6f5;
        border-radius: 8px;
        padding: 6px 11px;
        font-size: 0.82rem;
        color: #16327a;
        font-weight: 600;
    }
    .tarjeta-ubicacion {
        border: 1px dashed #16a34a;
        border-radius: 10px;
        padding: 10px 16px;
        background: #eafaf0;
        color: #15803d;
        font-weight: 600;
        margin-bottom: 14px;
    }
    div[data-baseweb="tab-list"] {
        gap: 6px;
        background: #eef1f8;
        padding: 6px;
        border-radius: 12px;
    }
    button[data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 600;
    }
    .footer-nota {
        text-align: center;
        color: #7c869b;
        font-size: 0.8rem;
        margin-top: 26px;
        padding-top: 14px;
        border-top: 1px solid #e2e6f0;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Datos ----------
with open("estaciones.json", "r", encoding="utf-8") as f:
    ESTACIONES = json.load(f)

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


def buscar_estaciones_cercanas(lat, lon, limite=3):
    resultados = []
    for est in ESTACIONES:
        distancia = haversine(lat, lon, est["lat"], est["lon"])
        resultados.append({
            "nombre": est["nombre"],
            "lat": est["lat"],
            "lon": est["lon"],
            "distancia_km": round(distancia, 2),
        })
    resultados.sort(key=lambda x: x["distancia_km"])
    return resultados[:limite]


def dibujar_mapa(lat, lon, resultados):
    mapa = folium.Map(location=[lat, lon], zoom_start=11, tiles=None, control_scale=True)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="Vista satelital",
        overlay=False,
        control=True,
    ).add_to(mapa)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Mapa de calles",
        overlay=False,
        control=True,
    ).add_to(mapa)

    icono_usuario = folium.CustomIcon("icono_usuario.png", icon_size=(38, 50), icon_anchor=(19, 50))
    folium.Marker(
        location=[lat, lon],
        tooltip="📍 Tu ubicación",
        icon=icono_usuario,
    ).add_to(mapa)

    puntos = [[lat, lon]]
    for r in resultados:
        icono_policia = folium.CustomIcon("icono_policia.png", icon_size=(42, 42), icon_anchor=(21, 21))
        folium.Marker(
            location=[r["lat"], r["lon"]],
            tooltip=f"🛡️ {r['nombre']} — {r['distancia_km']} km",
            icon=icono_policia,
        ).add_to(mapa)
        puntos.append([r["lat"], r["lon"]])

    mapa.fit_bounds(puntos, padding=(40, 40))
    folium.LayerControl(position="topright").add_to(mapa)
    return mapa


def mostrar_resultados(lat, lon, limite):
    resultados = buscar_estaciones_cercanas(lat, lon, limite)

    st.markdown(
        f'<div class="tarjeta-ubicacion">📍 Tu ubicación: {lat:.5f}, {lon:.5f}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("📋 Resultados")
    for i, r in enumerate(resultados, start=1):
        tiempos = estimar_tiempos(r["distancia_km"])
        pills = "".join(
            f'<span class="tiempo-pill">{modo} {formatear_minutos(min_)}</span>'
            for modo, min_ in tiempos.items()
        )
        st.markdown(f"""
        <div class="tarjeta-estacion">
            <span class="distancia">{r['distancia_km']} km</span>
            <span class="num">{i}</span>
            <span class="nombre">🛡️ {r['nombre']}</span>
            <div class="tiempos-fila">{pills}</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("⏱️ Tiempos estimados según distancia en línea recta y velocidad promedio de cada medio (no son rutas reales de calles ni horarios de bus).")

    st.subheader("🗺️ Mapa")
    mapa = dibujar_mapa(lat, lon, resultados)
    st_folium(mapa, width=None, height=460, returned_objects=[])


# ---------- Interfaz ----------
st.markdown(f"""
<div class="banner-policia">
    <h1>🚓 Estaciones Policiales Más Cercanas</h1>
    <p>Servicio en la nube que ubica las estaciones policiales reales más cercanas a tu posición
    en Honduras y estima cuánto tardarías en llegar a pie, en bici, en carro o en bus.</p>
    <div class="stats-fila">
        <span class="stat-chip">🛡️ {len(ESTACIONES)} estaciones registradas</span>
        <span class="stat-chip">🇭🇳 Cobertura nacional</span>
        <span class="stat-chip">🛰️ Vista satelital</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="seccion-card">', unsafe_allow_html=True)

limite = st.number_input("Cantidad de estaciones a mostrar", min_value=1, max_value=5, value=3)

tab_gps, tab_manual = st.tabs(["📡 Usar mi ubicación", "✍️ Escribir coordenadas"])

with tab_gps:
    st.write("Presiona el botón y acepta el permiso de ubicación que te pida el navegador.")

    if st.button("Usar mi ubicación actual"):
        st.session_state["quiere_gps"] = True
        st.session_state["gps_intento"] = st.session_state.get("gps_intento", 0) + 1

    if st.session_state.get("quiere_gps"):
        intento = st.session_state.get("gps_intento", 1)
        # Cada intento usa una llave distinta: así el componente se vuelve a montar
        # y le vuelve a pedir la ubicación al navegador en vez de quedarse pegado
        # con el resultado (o la falta de resultado) del primer intento.
        ubicacion = get_geolocation(component_key=f"geo_{intento}")
        if ubicacion is not None:
            lat = ubicacion["coords"]["latitude"]
            lon = ubicacion["coords"]["longitude"]
            st.success(f"Ubicación detectada: {lat:.6f}, {lon:.6f}")
            mostrar_resultados(lat, lon, limite)
        else:
            st.info("Obteniendo tu ubicación... acepta el permiso del navegador. Si no cambia en unos segundos, presiona de nuevo el botón (esto reintenta la solicitud).")

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

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-nota">Proyecto de clase — Cloud Computing, UTH · '
    'Estaciones policiales de Honduras (relevamiento propio del equipo)</div>',
    unsafe_allow_html=True,
)
