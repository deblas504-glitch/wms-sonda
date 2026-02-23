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

# --- 2. ESTILOS CSS REFINADOS (GLASSMORPHISM & GRADIENTS) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }

    /* Estilo Glassmorphism para los Botones de Cuentas */
    .stButton > button {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 15px;
        color: #1e293b;
        padding: 15px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        background-image: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        width: 100%;
    }

    .stButton > button:hover {
        background-image: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        color: white !important;
        transform: translateY(-2px);
        border: none;
    }

    /* Resaltado del botón activo (Simulado) */
    .active-filter {
        border: 2px solid #0284c7 !important;
        background-color: rgba(2, 132, 199, 0.1) !important;
    }

    /* KPI y Jarra */
    .kpi-container {
        display: flex; align-items: center; justify-content: center; gap: 60px;
        background: #ffffff; border-radius: 25px; padding: 40px; margin-bottom: 30px;
        border: 1px solid #f1f5f9; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .kpi-text-box h1 { font-size: 5rem !important; color: #0f172a !important; font-weight: 800 !important; letter-spacing: -3px; line-height: 0.8; }
    
    .water-sphere {
        width: 170px; height: 170px; background-color: #f8fafc; border-radius: 50%;
        position: relative; overflow: hidden; border: 2px solid #f1f5f9;
    }
    .wave {
        position: absolute; bottom: 0; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
        border-radius: 40%; animation: wave-animation 6s infinite linear; top: var(--wave-top); z-index: 2;
    }
    @keyframes wave-animation { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .water-percentage { position: absolute; width: 100%; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #1e293b; font-weight: 800; font-size: 1.5rem; z-index: 10; }
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

df_inv_raw, df_ent_raw, df_sal_raw = cargar_datos()

# --- 4. ESTADO DE SESIÓN PARA FILTROS ---
if 'cuenta_activa' not in st.session_state:
    st.session_state.cuenta_activa = "Todas"

# --- 5. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 1.5rem;'>📦 WMS SONDA</h1>", unsafe_allow_html=True)
    seccion = st.radio("NAVEGACIÓN", ["Inventario", "Entradas", "Salidas"])
    st.markdown("---")
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.session_state.cuenta_activa = "Todas"
        st.rerun()

# --- 6. SECCIÓN INVENTARIO ---
if seccion == "Inventario":
    st.subheader("📊 Control de Inventario")
    
    if not df_inv_raw.empty:
        # --- FILTROS GLASSMORPHISM (Cuentas) ---
        cuentas = ["Todas"] + sorted(df_inv_raw['Cuenta'].dropna().unique().tolist())
        st.markdown("##### Seleccionar Cuenta")
        
        # Grid de botones con estilo
        cols_cuentas = st.columns(5)
        for idx, nombre_cuenta in enumerate(cuentas):
            with cols_cuentas[idx % 5]:
                if st.button(nombre_cuenta, key=f"btn_{nombre_cuenta}"):
                    st.session_state.cuenta_activa = nombre_cuenta

        # Buscador y filtrado
        busqueda = st.text_input("🔍 Buscar en inventario:", placeholder="SKU, Lote, Ubicación...", key="search_inv")
        
        df_f = df_inv_raw.copy()
        if st.session_state.cuenta_activa != "Todas":
            df_f = df_f[df_f['Cuenta'] == st.session_state.cuenta_activa]
        if busqueda:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

        # KPIs y Jarra
        total_sel = df_f['Cantidad'].sum()
        total_global = df_inv_raw['Cantidad'].sum()
        pct = (total_sel / total_global * 100) if total_global > 0 else 0
        w_top = 100 - max(min(pct, 95), 5)

        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">PIEZAS EN {st.session_state.cuenta_activa.upper()}</p>
                    <h1>{total_sel:,.0f}</h1>
                </div>
                <div class="water-sphere">
                    <div class="water-percentage">{pct:.1f}%</div>
                    <div class="wave" style="--wave-top: {w_top}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(df_f, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay datos de inventario disponibles.")

# --- 7. SECCIONES MOVIMIENTOS ---
elif seccion in ["Entradas", "Salidas"]:
    st.subheader(f"📅 Historial de {seccion}")
    df_m = df_ent_raw if seccion == "Entradas" else df_sal_raw
    
    if not df_m.empty:
        c1, c2 = st.columns(2)
        f_ini = c1.date_input("Desde:", datetime.now() - timedelta(days=30), key=f"f1_{seccion}")
        f_fin = c2.date_input("Hasta:", datetime.now(), key=f"f2_{seccion}")
        
        df_m = df_m[(df_m['Fecha'].dt.date >= f_ini) & (df_m['Fecha'].dt.date <= f_fin)]
        st.dataframe(df_m, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de {seccion.lower()}.")