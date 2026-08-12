Estaciones Policiales Mas Cercanas

Aplicacion web hecha con Streamlit que ubica las estaciones policiales reales mas cercanas a tu posicion en Honduras y estima cuanto tardarias en llegar a pie, en bicicleta, en carro o en bus.

Que hace la app

- Detecta tu ubicacion actual usando el GPS del navegador, o permite escribir coordenadas manualmente.
- Calcula las estaciones policiales mas cercanas usando la formula de Haversine.
- Muestra un mapa interactivo con tu ubicacion y las estaciones cercanas, con vista satelital y vista de calles.
- Al hacer clic en una estacion del mapa, traza la ruta real por calles hasta ese punto y la muestra animada.
- Estima el tiempo de llegada segun el medio de transporte que elijas.

Tecnologias usadas

- Python
- Streamlit
- Folium y streamlit-folium para el mapa
- streamlit-js-eval para pedir la ubicacion del navegador
- API publica de OSRM para calcular rutas reales por calles
- requests para consumir la API de rutas

Archivos necesarios en la misma carpeta que app.py

- estaciones.json, con la lista de estaciones policiales (nombre, latitud, longitud)
- icono_usuario.png, icono del marcador de tu ubicacion
- icono_policia.png, icono del marcador de las estaciones
- policia-nacional-escudo.png, imagen de fondo del banner
- requirements.txt, con las librerias necesarias

Como correr el proyecto localmente

1. Instalar las dependencias
   pip install -r requirements.txt

2. Ejecutar la aplicacion
   streamlit run app.py

3. Abrir el navegador en la direccion que muestra la terminal, normalmente localhost 8501

Notas

La ubicacion por GPS depende de que el navegador y el sistema operativo tengan los permisos de ubicacion activados. En computadoras de escritorio sin wifi puede fallar; en celular funciona mejor por el GPS real del equipo.

Las rutas se calculan con un servicio publico y gratuito, por lo que puede tardar unos segundos o fallar si hay muchas solicitudes al mismo tiempo.

Proyecto academico, curso de Cloud Computing, UTH.
