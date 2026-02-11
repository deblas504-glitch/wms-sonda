import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="WMS Sonda", layout="wide")

# ==========================================
# 🔗 ENLACES DE GOOGLE SHEETS
# ==========================================
URL_INVENTARIO = "https://docs.google.com/spreadsheets/d/135jZiPzcgSz64NYybCYa8PIu8LAoyjk5IIn6NrEHjZ4/export?format=csv"
URL_ENTRADAS = "https://docs.google.com/spreadsheets/d/1mczk_zLZqypIXJY6uQqFj_5ioLHybasecxgNKzlopwc/export?format=csv"
URL_SALIDAS = "https://docs.google.com/spreadsheets/d/1aB-ODOa6-npqxX_WmWTOQuxYoWE1KxVAGNoSOcYoFck/export?format=csv" 

# --- 2. ESTILOS REFINADOS: JARRA REDONDA, OLA DINÁMICA Y FUENTE SUAVE ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        background-color: #ffffff;
    }
    
    /* Contenedor Principal de los KPIs */
    .kpi-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 80px;
        background: #ffffff;
        border-radius: 30px;
        padding: 50px;
        margin-bottom: 40px;
        border: 1px solid #f8fafc;
    }

    .kpi-text-box h1 { 
        font-size: 5.5rem !important; 
        color: #0f172a !important; 
        margin: 0; 
        font-weight: 800 !important;
        letter-spacing: -4px;
        line-height: 0.9;
    }

    .label-kpi {
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    /* LA JARRA REDONDA (ESFERA) */
    .water-sphere {
        width: 190px;
        height: 190px;
        background-color: #f1f5f9;
        border-radius: 50%;
        position: relative;
        overflow: hidden;
        border: 1px solid #f1f5f9; /* Delineado casi imperceptible */
        box-shadow: inset 0 5px 15px rgba(0,0,0,0.03), 0 10px 30px rgba(0,0,0,0.02);
    }

    /* EL EFECTO DE OLA DINÁMICO */
    .wave {
        position: absolute;
        bottom: 0;
        left: -50%;
        width: 200%;
        height: 200%;
        background: rgba(2, 132, 199, 0.85); /* Azul más fuerte */
        border-radius: 40%;
        animation: wave-animation 7s infinite linear;
        transition: top 1.5s cubic-bezier(0.4, 0, 0.2, 1);
        top: var(--wave-top);
        z-index: 2;
    }

    .wave-back {
        background: rgba(125, 211, 252, 0.4); /* Azul claro de fondo */
        animation: wave-animation 11s infinite linear;
        border-radius: 35%;
        z-index: 1;
        top: calc(var(--wave-top) - 4%);
    }

    @keyframes wave-animation {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* TEXTO DENTRO DE LA JARRA */
    .water-percentage {
        position: absolute;
        width: 100%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        color: #1e293b;
        font-weight: 400; /* Fuente suave */
        font-size: 1.7rem;
        z-index: 10;
        pointer-events: none;
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }

    /* Botones de Cuentas Estilizados */
    div.stButton > button {
        background-color: #ffffff;
        color: #64748b;
        border: 1px solid #f1f5f9;
        border-radius: 15px;
        padding: 10px 20px;
        font-weight: 600 !important;
        transition: all 0.3s ease;
        font-size: 0.85rem;
    }
    div.stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #0369a1 !important;
        background-color: #f0f9ff !important;
    }

    /* Quitar bordes de la tabla de Streamlit */
    [data-testid="stDataFrame"] {
        border: none !important;
    }
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

# --- 4. ESTADO DE LA SESIÓN ---
if 'cuenta_f' not in st.session_state:
    st.session_state.cuenta_f = "Todas"

# --- 5. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.4rem; color: #0f172a; font-weight: 800; margin-bottom: 20px;'>WMS SONDA</h2>", unsafe_allow_html=True)
    opcion = st.radio("SECCIONES", ["Inventario", "Entradas", "Salidas"])
    st.markdown("---")
    if st.button("🔄 Sincronizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.cuenta_f = "Todas"
        st.rerun()

# --- 6. FUNCIÓN DE INTERFAZ DINÁMICA ---
def mostrar_interfaz(titulo, df_raw, key_s, usa_fechas=False):
    df = df_raw.copy()
    if not df.empty:
        # --- Selector de Cuentas ---
        cuentas = ["Todas"] + sorted(df['Cuenta'].unique().tolist()) if 'Cuenta' in df.columns else ["Todas"]
        st.markdown(f"### Filtrar por Cuenta")
        
        n_cols = 6
        for i in range(0, len(cuentas), n_cols):
            fila = cuentas[i : i + n_cols]
            cols = st.columns(n_cols)
            for j, nombre in enumerate(fila):
                with cols[j]:
                    # Resaltar botón seleccionado (opcional, aquí simple)
                    if st.button(nombre, key=f"btn_{nombre}_{key_s}", use_container_width=True):
                        st.session_state.cuenta_f = nombre

        if usa_fechas:
            st.markdown("#### Rango de Consulta")
            f1, f2 = st.columns(2)
            start_d = f1.date_input("Desde:", datetime.now() - timedelta(days=30), key=f"s_{key_s}")
            end_d = f2.date_input("Hasta:", datetime.now(), key=f"e_{key_s}")
            df = df[(df['Fecha'].dt.date >= start_d) & (df['Fecha'].dt.date <= end_d)]

        # --- Lógica de Cálculos para la Jarra ---
        total_global = df['Cantidad'].sum()
        
        if st.session_state.cuenta_f != "Todas":
            df_mostrar = df[df['Cuenta'] == st.session_state.cuenta_f]
        else:
            df_mostrar = df
        
        total_seleccionado = df_mostrar['Cantidad'].sum()
        porcentaje = (total_seleccionado / total_global * 100) if total_global > 0 else 0
        
        # Ajuste visual para que la ola siempre se vea (entre 5% y 95%)
        wave_top_val = 100 - max(min(porcentaje, 95), 5)

        # --- KPI CON JARRA REDONDA Y OLA ---
        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">PIEZAS EN {st.session_state.cuenta_f}</p>
                    <h1>{total_seleccionado:,.0f}</h1>
                </div>
                <div class="water-sphere">
                    <div class="water-percentage">{porcentaje:.1f}%</div>
                    <div class="wave wave-back" style="--wave-top: {wave_top_val}%;"></div>
                    <div class="wave" style="--wave-top: {wave_top_val}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- Buscador y Tabla de Datos ---
        q = st.text_input(f"🔍 Buscar en {st.session_state.cuenta_f}...", placeholder="SKU, descripción, lote...", key=f"q_{key_s}")
        if q:
            mask = df_mostrar.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            df_mostrar = df_mostrar[mask]

        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        # Exportación
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w: 
            df_mostrar.to_excel(w, index=False)
        st.download_button(f"📥 Descargar Reporte Excel", buf.getvalue(), f"Reporte_{key_s}.xlsx", use_container_width=True)
        
    else:
        st.warning("No se encontraron datos para mostrar.")

# --- 7. EJECUCIÓN SEGÚN SECCIÓN ---
if opcion == "Inventario":
    mostrar_interfaz("Inventario", df_inv_raw, "inv")
elif opcion == "Entradas":
    mostrar_interfaz("Entradas", df_ent_raw, "ent", True)
elif opcion == "Salidas":
    mostrar_interfaz("Salidas", df_sal_raw, "sal", True)