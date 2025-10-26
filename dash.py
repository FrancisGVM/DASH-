import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # Para generar datos de ejemplo

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Ventas REEM",
    layout="wide"
)


sectores = [
        "Agricultura, ganadería, silvicultura y pesca", "Comercio", "Construcción",
        "Explotación de Minas y Canteras", "Industrias Manufactureras", "Servicios"
    ]


df = pd.read_excel(r"ventas_dash.xlsx")
df['canton-unico'] = df['codigo_canton'].astype(str) + " - " + df['canton']
cantones = df.sort_values(by="canton", ascending=True)["canton-unico"].unique().tolist()


# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros del Dashboard")

sector_seleccionado = st.sidebar.selectbox(
    "Selecciona un Sector:",
    options=sectores
)

canton_seleccionado = st.sidebar.selectbox(
    "Selecciona un Cantón:",
    options=cantones
)


escala_seleccionada = st.sidebar.radio(
    "Selecciona la Escala del Eje Y:",
    options=["Lineal", "Logarítmica"],
    help="La escala logarítmica es útil cuando los datos están muy polarizados."
)

# 1. Filtrar los datos por el sector elegido
df_filtrado = df[df["gsectores"] == sector_seleccionado].copy()

# 2. Agrupar por cantón y sumar las ventas.
# ESTE ES EL PASO CLAVE: Ordenar de menor a mayor y resetear el índice
# El índice ahora representa el "ranking"
df_ventas = df_filtrado.groupby("canton-unico")["TotVTA"].sum().sort_values().reset_index()

# 3. Verificar si el cantón seleccionado tiene ventas en este sector
if canton_seleccionado not in df_ventas["canton-unico"].values:
    st.warning(f"La ciudade '{canton_seleccionado}' no tiene ventas registradas para el sector '{sector_seleccionado}'.")
    # Creamos un dataframe vacío para que el gráfico no falle
    df_display = pd.DataFrame(columns=["canton-unico", "TotVTA", "Color"])

else:
    # 4. Encontrar el ÍNDICE (la posición en el ranking) del cantón seleccionado
    idx_seleccionado = df_ventas[df_ventas["canton-unico"] == canton_seleccionado].index[0]

    # 5. Identificar los 5 vecinos INFERIORES (índices antes del seleccionado)
    # Usamos max(0, ...) para evitar índices negativos si está cerca del inicio
    start_idx_abajo = max(0, idx_seleccionado - 5)
    df_vecinos_abajo = df_ventas.iloc[start_idx_abajo : idx_seleccionado]

    # 6. Identificar los 5 vecinos SUPERIORES (índices después del seleccionado)
    # Python maneja automáticamente si nos pasamos del final de la lista
    end_idx_arriba = idx_seleccionado + 1 + 5
    df_vecinos_arriba = df_ventas.iloc[idx_seleccionado + 1 : end_idx_arriba]

    # 7. Obtener la fila del cantón seleccionado (usamos [[]] para que sea un DataFrame)
    df_seleccionado = df_ventas.iloc[[idx_seleccionado]]

    # 8. Combinar los dataframes para la visualización
    df_display = pd.concat([
        df_vecinos_abajo,
        df_seleccionado,
        df_vecinos_arriba
    ]).sort_values(by="TotVTA")

    # 9. Añadir una columna para colorear el gráfico (NUEVA LÓGICA DE COLOR)
    def asignar_color(canton_actual):
        if canton_actual == canton_seleccionado:
            return "Seleccionado"
        elif canton_actual in df_vecinos_arriba["canton-unico"].values:
            return "Vecinos Superiores"
        elif canton_actual in df_vecinos_abajo["canton-unico"].values:
            return "Vecinos Inferiores"
        return "Otro" # No debería pasar

    df_display["Color"] = df_display["canton-unico"].apply(asignar_color)


# --- TÍTULO PRINCIPAL ---
st.title(f"Análisis de Ventas para el Sector: {sector_seleccionado}")

if not df_display.empty:
    st.markdown(f"Mostrando: **{canton_seleccionado}** en comparación con sus 5 vecinos superiores e inferiores en el ranking de ventas.")
    
    # --- GRÁFICO (El "Recuadro" que pediste) ---

    # Definimos los nuevos colores
    color_map = {
        "Seleccionado": "orange",
        "Vecinos Superiores": "green",
        "Vecinos Inferiores": "red"
    }

    fig = px.bar(
        df_display,
        x="canton-unico",
        y="TotVTA",
        title=f"Ventas por Cantón (Sector: {sector_seleccionado})",
        color="Color", # Colorea la barra según la nueva categoría
        color_discrete_map=color_map, # Aplica los nuevos colores
        labels={"Ventas": "Ventas Totales (USD)"}
    )

    # 7. Aplicar la escala (Lineal o Logarítmica)
    if escala_seleccionada == "Logarítmica":
        fig.update_yaxes(type="log")
    else:
        fig.update_yaxes(type="linear")

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # --- Opcional: Mostrar la tabla de datos ---
    st.dataframe(df_display, use_container_width=True)

else:
    st.info("No hay datos para mostrar con los filtros seleccionados.")