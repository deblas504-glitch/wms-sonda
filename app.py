import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="WMS Sonda", layout="wide")

# ==========================================
# 🔗 ENLACES DE GOOGLE SHEETS
# ==========================================
URL_INVENTARIO = "https://docs.google.com/spreadsheets/d/135jZiPzcgSz64NYybCYa8PIu8LAoyjk5IIn6NrEHjZ4/export?format=csv"
URL_ENTRADAS = "https://docs.google.com/spreadsheets/d/1mczk_zLZqypIXJY6uQqFj_5ioLHybasecxgNKzlopwc/export?format=csv"
URL_SALIDAS = "https://docs.google.com/spreadsheets/d/1aB-ODOa6-npqxX_WmWTOQuxYoWE1KxVAGNoSOcYoFck/export?format=csv" 

# --- 2. ESTILOS ELEGANTES (FILTROS DE PALETA) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp { background-color: #ffffff; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 1px solid #eeeeee;
    }

    /* Estilo para los botones que parecen paletas */
    div.stButton > button {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 15px;
        width: 100%;
        height: auto;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    /* Efecto Verde Aceptado al pasar el mouse */
    div.stButton > button:hover {
        border-color: #22c55e !important;
        color: #15803d !important;
        background-color: #f0fdf4 !important;
        transform: translateY(-3px);
        box-shadow: 0 10px 15px rgba(34, 197, 94, 0.1);
    }

    /* Estilo cuando el botón está seleccionado (ficticio vía lógica) */
    div.stButton > button:focus {
        border-color: #22c55e !important;
        background-color: #f0fdf4 !important;
    }

    h1 { font-size: 2.5rem !important; font-weight: 800 !important; color: #0f172a !important; }
    
    /* Contenedor de métricas dentro del botón */
    .btn-text { font-size: 0.9rem; font-weight: 600; display: block; }
    .btn-sub { font-size: 0.75rem; font-weight: 400; color: #64748b; display: block; }

    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    def fetch(url):
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            return df
        except:
            return pd.DataFrame()
    return fetch(URL_INVENTARIO), fetch(URL_ENTRADAS), fetch(URL_SALIDAS)

df_inv_raw, df_ent_raw, df_sal_raw = cargar_datos()

# --- 4. ESTADO DE FILTRO ---
if 'cuenta_seleccionada' not in st.session_state:
    st.session_state.cuenta_seleccionada = "Todas"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.4rem; color: #0f172a;'>SONDA WMS</h2>", unsafe_allow_html=True)
    opcion = st.radio("SECCIONES", ["Inventario", "Entradas", "Salidas"])
    if st.button("Sincronizar Datos"):
        st.cache_data.clear()
        st.session_state.cuenta_seleccionada = "Todas"
        st.rerun()

# --- 6. FUNCIÓN DE VISTA DINÁMICA ---
def mostrar_vista(titulo, df_raw, key_suffix):
    st.title(titulo)
    df = df_raw.copy()
    
    if not df.empty:
        # Calcular cuentas y sus cantidades
        cuentas_data = df.groupby('Cuenta')['Cantidad'].sum().reset_index()
        total_piezas = df['Cantidad'].sum()
        
        st.markdown("### Cuentas")
        
        # Crear fila de paletas (botones)
        # Usamos columnas para que no ocupen todo el ancho
        cuentas_lista = ["Todas"] + cuentas_data['Cuenta'].tolist()
        cols = st.columns(min(len(cuentas_lista), 6)) # Máximo 6 paletas por fila para no saturar
        
        for i, nombre in enumerate(cuentas_lista):
            col_idx = i % 6
            with cols[col_idx]:
                if nombre == "Todas":
                    label = f"Todas\n({total_piezas:,.0f})"
                else:
                    cant = cuentas_data[cuentas_data['Cuenta'] == nombre]['Cantidad'].values[0]
                    label = f"{nombre}\n({cant:,.0f})"
                
                # El botón actúa como filtro directo
                if st.button(label, key=f"btn_{nombre}_{key_suffix}"):
                    st.session_state.cuenta_seleccionada = nombre

        # Aplicar filtro
        if st.session_state.cuenta_seleccionada != "Todas":
            df = df[df['Cuenta'] == st.session_state.cuenta_seleccionada]

        st.info(f"Viendo: **{st.session_state.cuenta_seleccionada}**")

        # Buscador
        q = st.text_input("Buscador universal (SKU, Descripción...)", key=f"q_{key_suffix}")
        if q:
            mask = df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            df = df[mask]

        # Tabla y Exportación
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w: df.to_excel(w, index=False)
        st.download_button("Descargar Excel", buf.getvalue(), f"{key_suffix}.xlsx")

    else:
        st.warning("No hay datos para mostrar.")

# Ejecución
if opcion == "Inventario":
    mostrar_vista("Inventario General", df_inv_raw, "inv")
elif opcion == "Entradas":
    mostrar_vista("Entradas de Mercancía", df_ent_raw, "ent")
elif opcion == "Salidas":
    mostrar_vista("Salidas de Mercancía", df_sal_raw, "sal")