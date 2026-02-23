import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="WMS Sonda Pro", layout="wide", page_icon="📦")

# ==========================================
# 🔗 ENLACES DE GOOGLE SHEETS
# ==========================================
URL_INVENTARIO = "https://docs.google.com/spreadsheets/d/135jZiPzcgSz64NYybCYa8PIu8LAoyjk5IIn6NrEHjZ4/export?format=csv"
URL_ENTRADAS = "https://docs.google.com/spreadsheets/d/1mczk_zLZqypIXJY6uQqFj_5ioLHybasecxgNKzlopwc/export?format=csv"
URL_SALIDAS = "https://docs.google.com/spreadsheets/d/1aB-ODOa6-npqxX_WmWTOQuxYoWE1KxVAGNoSOcYoFck/export?format=csv" 

# --- 2. ESTILOS CSS: GLASSMORPHISM & GRADIENTES ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }

    /* BOTONES DE CUENTAS (GLASSMORPHISM) */
    div.stButton > button {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 20px;
        color: #1e293b;
        padding: 15px 10px;
        font-weight: 700;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        background-image: linear-gradient(135deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.2) 100%);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        width: 100%;
        height: 70px;
        text-transform: uppercase;
        font-size: 0.8rem;
    }

    div.stButton > button:hover {
        background-image: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important;
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
        border: none;
    }

    /* KPI CONTAINER & JARRA */
    .kpi-container {
        display: flex; align-items: center; justify-content: center; gap: 60px;
        background: #ffffff; border-radius: 30px; padding: 35px; margin-top: 15px;
        border: 1px solid #f8fafc; box-shadow: 0 10px 30px rgba(0,0,0,0.02);
    }
    .kpi-text-box h1 { font-size: 4.5rem !important; color: #0f172a !important; font-weight: 800 !important; letter-spacing: -3px; line-height: 0.9; margin: 0; }
    
    .water-sphere {
        width: 150px; height: 150px; background-color: #f1f5f9; border-radius: 50%;
        position: relative; overflow: hidden; border: 1px solid #e2e8f0;
    }
    .wave {
        position: absolute; bottom: 0; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
        border-radius: 43%; animation: wave-animation 8s infinite linear; 
        top: var(--wave-top); transition: top 1.5s ease-in-out;
    }
    @keyframes wave-animation { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .water-percentage { position: absolute; width: 100%; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #1e293b; font-weight: 700; font-size: 1.4rem; z-index: 10; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    def fetch(url):
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.astype(str).str.strip()
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            return df
        except: return pd.DataFrame()
    return fetch(URL_INVENTARIO), fetch(URL_ENTRADAS), fetch(URL_SALIDAS)

df_inv, df_ent, df_sal = cargar_datos()

# --- 4. ESTADO DE SESIÓN ---
if 'cuenta_f' not in st.session_state:
    st.session_state.cuenta_f = "Todas"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-weight: 800;'>WMS SONDA</h2>", unsafe_allow_html=True)
    seccion = st.radio("NAVEGACIÓN", ["Inventario", "Entradas", "Salidas"])
    st.markdown("---")
    if st.button("🔄 Sincronizar Todo"):
        st.cache_data.clear()
        st.session_state.cuenta_f = "Todas"
        st.rerun()

# --- 6. FUNCIÓN DE INTERFAZ UNIFICADA ---
def renderizar_seccion(df_original, titulo_seccion, mostrar_jarra=False):
    if df_original.empty:
        st.error(f"No hay datos disponibles en {titulo_seccion}.")
        return

    # Blindaje de la columna "Cuentas"
    col_target = "Cuentas"
    if col_target not in df_original.columns:
        st.error(f"⚠️ No se encontró la columna '{col_target}' en esta hoja.")
        st.info(f"Columnas detectadas: {list(df_original.columns)}")
        return

    # --- FILTRO VISUAL DE CAJAS ---
    cuentas_list = ["Todas"] + sorted(df_original[col_target].dropna().unique().tolist())
    st.markdown(f"### Filtrar {titulo_seccion} por Cuenta")
    
    n_cols = 5
    for i in range(0, len(cuentas_list), n_cols):
        fila = cuentas_list[i:i + n_cols]
        cols = st.columns(n_cols)
        for idx, nombre in enumerate(fila):
            # Key única por sección y nombre para evitar conflictos
            if cols[idx].button(nombre, key=f"btn_{titulo_seccion}_{nombre}"):
                st.session_state.cuenta_f = nombre

    st.markdown("---")

    # Filtros adicionales
    c1, c2 = st.columns([2, 1])
    with c1:
        q = st.text_input(f"🔍 Buscar en {st.session_state.cuenta_f}:", key=f"q_{titulo_seccion}")
    
    # Lógica de filtrado
    df_f = df_original.copy()
    if st.session_state.cuenta_f != "Todas":
        df_f = df_f[df_f[col_target] == st.session_state.cuenta_f]
    if q:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]

    # Mostrar Jarra y KPI si es Inventario
    if mostrar_jarra:
        total_p = df_f['Cantidad'].sum()
        total_g = df_original['Cantidad'].sum()
        pct = (total_p / total_g * 100) if total_g > 0 else 0
        w_top = 100 - max(min(pct, 95), 5)

        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">PIEZAS EN {st.session_state.cuenta_f.upper()}</p>
                    <h1>{total_p:,.0f}</h1>
                </div>
                <div class="water-sphere">
                    <div class="water-percentage">{pct:.1f}%</div>
                    <div class="wave" style="--wave-top: {w_top}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Para Entradas/Salidas mostrar solo un KPI simple o contador
        total_mov = df_f['Cantidad'].sum()
        st.metric(f"Total Unidades ({st.session_state.cuenta_f})", f"{total_mov:,.0f}")

    st.dataframe(df_f, use_container_width=True, hide_index=True)

# --- 7. EJECUCIÓN ---
if seccion == "Inventario":
    renderizar_seccion(df_inv, "Inventario", mostrar_jarra=True)
elif seccion == "Entradas":
    renderizar_seccion(df_ent, "Entradas")
elif seccion == "Salidas":
    renderizar_seccion(df_sal, "Salidas")