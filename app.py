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
        background-color: #ffffff;
    }

    /* Estilo Glassmorphism para los Botones de Cuentas */
    div.stButton > button {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        color: #1e293b;
        padding: 12px 20px;
        font-weight: 600;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        background-image: linear-gradient(135deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.2) 100%);
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    div.stButton > button:hover {
        background-image: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
        color: white !important;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(2, 132, 199, 0.3);
        border: none;
    }

    /* KPI CONTAINER */
    .kpi-container {
        display: flex; align-items: center; justify-content: center; gap: 80px;
        background: #ffffff; border-radius: 30px; padding: 50px; margin-bottom: 40px;
        border: 1px solid #f8fafc; box-shadow: 0 10px 30px rgba(0,0,0,0.02);
    }
    .kpi-text-box h1 { 
        font-size: 5.5rem !important; color: #0f172a !important; 
        font-weight: 800 !important; letter-spacing: -4px; line-height: 0.9;
        margin: 0;
    }
    .label-kpi { color: #94a3b8; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; }
    
    /* LA JARRA REDONDA */
    .water-sphere {
        width: 190px; height: 190px; background-color: #f1f5f9; border-radius: 50%;
        position: relative; overflow: hidden; border: 1px solid #f1f5f9;
        box-shadow: inset 0 5px 15px rgba(0,0,0,0.03);
    }
    .wave {
        position: absolute; bottom: 0; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
        border-radius: 40%; animation: wave-animation 7s infinite linear; 
        top: var(--wave-top); z-index: 2; transition: top 1.5s ease-in-out;
    }
    @keyframes wave-animation { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .water-percentage { 
        position: absolute; width: 100%; top: 50%; left: 50%; transform: translate(-50%, -50%); 
        text-align: center; color: #1e293b; font-weight: 700; font-size: 1.7rem; z-index: 10; 
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. CARGA DE DATOS (CON LIMPIEZA DE COLUMNAS) ---
@st.cache_data(ttl=60)
def cargar_datos():
    def fetch(url):
        try:
            df = pd.read_csv(url)
            # Limpieza de nombres de columnas para evitar KeyError
            df.columns = df.columns.astype(str).str.strip().str.capitalize()
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            return df
        except: return pd.DataFrame()
    return fetch(URL_INVENTARIO), fetch(URL_ENTRADAS), fetch(URL_SALIDAS)

df_inv_raw, df_ent_raw, df_sal_raw = cargar_datos()

# --- 4. ESTADO DE SESIÓN ---
if 'cuenta_f' not in st.session_state:
    st.session_state.cuenta_f = "Todas"

# --- 5. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.4rem; font-weight: 800;'>WMS SONDA</h2>", unsafe_allow_html=True)
    seccion = st.radio("SECCIONES", ["Inventario", "Entradas", "Salidas"])
    st.markdown("---")
    if st.button("🔄 Sincronizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.cuenta_f = "Todas"
        st.rerun()

# --- 6. SECCIÓN INVENTARIO ---
if seccion == "Inventario":
    if not df_inv_raw.empty:
        # --- FILTROS GLASSMORPHISM ---
        # Buscamos la columna 'Cuenta' sin importar si está en minúsculas
        col_cuenta = 'Cuenta' if 'Cuenta' in df_inv_raw.columns else df_inv_raw.columns[0]
        
        cuentas = ["Todas"] + sorted(df_inv_raw[col_cuenta].dropna().unique().tolist())
        
        st.markdown("### Filtrar por Cuenta")
        n_cols = 5
        for i in range(0, len(cuentas), n_cols):
            fila_cuentas = cuentas[i : i + n_cols]
            cols = st.columns(n_cols)
            for j, nombre in enumerate(fila_cuentas):
                with cols[j]:
                    if st.button(nombre, key=f"btn_{nombre}"):
                        st.session_state.cuenta_f = nombre

        # Lógica de filtrado
        busqueda = st.text_input("🔍 Buscar SKU, Lote o Ubicación:", key="q_inv")
        
        df_f = df_inv_raw.copy()
        if st.session_state.cuenta_f != "Todas":
            df_f = df_f[df_f[col_cuenta] == st.session_state.cuenta_f]
        if busqueda:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

        # KPIs y Jarra
        total_sel = df_f['Cantidad'].sum() if 'Cantidad' in df_f.columns else 0
        total_global = df_inv_raw['Cantidad'].sum() if 'Cantidad' in df_inv_raw.columns else 1
        pct = (total_sel / total_global * 100)
        w_top = 100 - max(min(pct, 95), 5)

        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">PIEZAS EN {st.session_state.cuenta_f}</p>
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
        st.error("No se pudo leer la columna 'Cuenta'. Verifica tu Google Sheets.")

# --- 7. SECCIONES ENTRADAS / SALIDAS ---
elif seccion in ["Entradas", "Salidas"]:
    df_m = df_ent_raw if seccion == "Entradas" else df_sal_raw
    if not df_m.empty:
        st.markdown(f"### Historial de {seccion}")
        c1, c2 = st.columns(2)
        f1 = c1.date_input("Desde:", datetime.now() - timedelta(days=30), key=f"f1_{seccion}")
        f2 = c2.date_input("Hasta:", datetime.now(), key=f"f2_{seccion}")
        
        # Filtrado por fecha
        if 'Fecha' in df_m.columns:
            df_m = df_m[(df_m['Fecha'].dt.date >= f1) & (df_m['Fecha'].dt.date <= f2)]
            
        st.dataframe(df_m, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No hay datos para {seccion}.")