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

# --- 2. ESTILOS REFINADOS (NEGRITAS Y ELEGANCIA) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }
    .stApp { background-color: #ffffff; }
    
    /* Tarjeta Maestra de Piezas Totales */
    .main-kpi {
        background: #ffffff;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        border: 1px solid #f1f5f9;
        box-shadow: 0 10px 30px rgba(0,0,0,0.02);
        margin-bottom: 30px;
    }
    .main-kpi p { 
        text-transform: uppercase; 
        letter-spacing: 0.15rem; 
        color: #475569 !important; 
        font-size: 0.95rem;
        font-weight: 700 !important;
        margin-bottom: 10px;
    }
    .main-kpi h1 { 
        font-size: 4.5rem !important; 
        color: #0f172a !important; 
        margin: 0; 
        font-weight: 900 !important;
    }

    /* Estilo de los Botones (Paletas) */
    div.stButton > button {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
        font-weight: 800 !important;
        transition: all 0.3s ease;
        margin-bottom: 5px;
    }
    
    div.stButton > button:hover {
        border-color: #22c55e !important;
        background-color: #f0fdf4 !important;
        color: #15803d !important;
        transform: translateY(-2px);
    }

    /* Títulos de sección */
    h3 { 
        color: #0f172a !important; 
        font-weight: 800 !important;
        font-size: 1.6rem !important;
    }

    /* Menú lateral (Sidebar) */
    [data-testid="stSidebar"] { background-color: #fcfcfc !important; }
    [data-testid="stSidebar"] label {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* Ajuste para inputs de fecha (Minimalista) */
    .stDateInput label {
        font-weight: 700 !important;
        color: #475569 !important;
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

# --- 4. ESTADO DE SESIÓN ---
if 'cuenta_f' not in st.session_state:
    st.session_state.cuenta_f = "Todas"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.3rem; color: #0f172a; font-weight: 900; letter-spacing: -0.05rem;'>SONDA WMS</h2>", unsafe_allow_html=True)
    opcion = st.radio("SECCIONES", ["Inventario", "Entradas", "Salidas"])
    st.write("---")
    if st.button("🔄 Sincronizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.cuenta_f = "Todas"
        st.rerun()

# --- 6. FUNCIÓN DE INTERFAZ PRINCIPAL ---
def mostrar_interfaz(titulo, df_raw, key_s, usa_fechas=False):
    df = df_raw.copy()
    
    if not df.empty:
        cuentas = ["Todas"] + sorted(df['Cuenta'].unique().tolist()) if 'Cuenta' in df.columns else ["Todas"]
        
        st.markdown(f"### Cuentas en {titulo}")
        
        # DISTRIBUCIÓN SIMÉTRICA (5 columnas)
        n_cols = 5
        for i in range(0, len(cuentas), n_cols):
            fila_cuentas = cuentas[i : i + n_cols]
            cols = st.columns(n_cols)
            
            for j, nombre in enumerate(fila_cuentas):
                with cols[j]:
                    if st.button(nombre, key=f"btn_{nombre}_{key_s}", use_container_width=True):
                        st.session_state.cuenta_f = nombre
        
        st.write(" ") 

        # --- FILTRO DE FECHAS (Solo si aplica) ---
        if usa_fechas and 'Fecha' in df.columns:
            st.markdown("#### Rango de Consulta")
            f1, f2 = st.columns(2)
            # Default: últimos 30 días
            start_d = f1.date_input("Desde:", datetime.now() - timedelta(days=30), key=f"start_{key_s}")
            end_d = f2.date_input("Hasta:", datetime.now(), key=f"end_{key_s}")
            
            # Aplicamos el filtro de fecha antes que el de cuenta para consistencia
            df = df[(df['Fecha'].dt.date >= start_d) & (df['Fecha'].dt.date <= end_d)]

        # Aplicar Filtro de Cuenta seleccionado
        if st.session_state.cuenta_f != "Todas":
            df = df[df['Cuenta'] == st.session_state.cuenta_f]
        
        # INDICADOR MAESTRO (KPI)
        piezas_mostradas = df['Cantidad'].sum()
        st.markdown(f"""
            <div class="main-kpi">
                <p>Piezas Totales en {st.session_state.cuenta_f}</p>
                <h1>{piezas_mostradas:,.0f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Buscador Universal
        q = st.text_input(f"Buscador en {st.session_state.cuenta_f}", placeholder="SKU, Descripción, Folio...", key=f"q_{key_s}")
        if q:
            mask = df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)
        
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w: df.to_excel(w, index=False)
        st.download_button(f"📥 Exportar {st.session_state.cuenta_f} a Excel", buf.getvalue(), f"{key_s}_{st.session_state.cuenta_f}.xlsx", use_container_width=True)
    else:
        st.warning("No se encontraron datos.")

# --- 7. EJECUCIÓN ---
if opcion == "Inventario":
    # Inventario suele ser "estático" al día de hoy, no lleva rango de fechas
    mostrar_interfaz("Inventario", df_inv_raw, "inv", usa_fechas=False)
elif opcion == "Entradas":
    mostrar_interfaz("Entradas", df_ent_raw, "ent", usa_fechas=True)
elif opcion == "Salidas":
    mostrar_interfaz("Salidas", df_sal_raw, "sal", usa_fechas=True)