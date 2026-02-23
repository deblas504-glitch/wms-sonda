import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="WMS Sonda Pro", layout="wide", page_icon="📦")

# ==========================================
# 🔗 ENLACES DE GOOGLE SHEETS (CSV)
# ==========================================
URL_INVENTARIO = "https://docs.google.com/spreadsheets/d/135jZiPzcgSz64NYybCYa8PIu8LAoyjk5IIn6NrEHjZ4/export?format=csv"
URL_ENTRADAS = "https://docs.google.com/spreadsheets/d/1mczk_zLZqypIXJY6uQqFj_5ioLHybasecxgNKzlopwc/export?format=csv"
URL_SALIDAS = "https://docs.google.com/spreadsheets/d/1aB-ODOa6-npqxX_WmWTOQuxYoWE1KxVAGNoSOcYoFck/export?format=csv" 

# --- 2. ESTILOS CSS (Jarra Redonda y Ola) ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .kpi-container {
        display: flex; align-items: center; justify-content: center; gap: 60px;
        background: #ffffff; border-radius: 25px; padding: 40px; margin-bottom: 30px;
        border: 1px solid #f1f5f9; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .kpi-text-box h1 { 
        font-size: 5rem !important; color: #0f172a !important; margin: 0; 
        font-weight: 800 !important; letter-spacing: -3px; line-height: 0.8;
    }
    .label-kpi { color: #94a3b8; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; }
    
    .water-sphere {
        width: 170px; height: 170px; background-color: #f8fafc; border-radius: 50%;
        position: relative; overflow: hidden; border: 2px solid #f1f5f9;
    }
    .wave {
        position: absolute; bottom: 0; left: -50%; width: 200%; height: 200%;
        background: rgba(2, 132, 199, 0.8); border-radius: 40%;
        animation: wave-animation 6s infinite linear; top: var(--wave-top); z-index: 2;
        transition: top 1s ease-in-out;
    }
    .wave-back { background: rgba(125, 211, 252, 0.4); animation: wave-animation 9s infinite linear; z-index: 1; top: calc(var(--wave-top) - 5%); }
    @keyframes wave-animation { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .water-percentage {
        position: absolute; width: 100%; top: 50%; left: 50%; transform: translate(-50%, -50%);
        text-align: center; color: #1e293b; font-weight: 800; font-size: 1.5rem; z-index: 10;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    def fetch(url):
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.astype(str).str.strip() # Limpia nombres de columnas
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            return df
        except:
            return pd.DataFrame()
    return fetch(URL_INVENTARIO), fetch(URL_ENTRADAS), fetch(URL_SALIDAS)

df_inv_raw, df_ent_raw, df_sal_raw = cargar_datos()

# --- 4. MOTOR DE PICKING (LÓGICA DE LA MACRO) ---
def motor_surtido(df_inv, sku, cant_pedida):
    # Filtramos stock disponible para ese SKU
    stock_disponible = df_inv[(df_inv['SKU'] == sku) & (df_inv['Cantidad'] > 0)].copy()
    asignacion = []
    pendiente = cant_pedida
    
    for _, fila in stock_disponible.iterrows():
        if pendiente <= 0: break
        tomar = min(fila['Cantidad'], pendiente)
        asignacion.append({
            "SKU": sku,
            "Lote": fila.get('Lote', 'N/A'),
            "Ubicación": fila.get('Ubicación', 'N/A'),
            "Cantidad Surtida": tomar
        })
        pendiente -= tomar
    
    return pd.DataFrame(asignacion), pendiente

# --- 5. BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2271/2271068.png", width=80)
    st.markdown("<h1 style='font-size: 1.2rem;'>SISTEMA WMS SONDA</h1>", unsafe_allow_html=True)
    seccion = st.radio("NAVEGACIÓN", ["🏠 Inventario", "📅 Movimientos", "⚡ Surtido Rápido"])
    st.markdown("---")
    if st.button("🔄 Sincronizar Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. SECCIÓN 1: INVENTARIO CON JARRA DINÁMICA ---
if seccion == "🏠 Inventario":
    st.header("Estado Actual de Bodega")
    
    if not df_inv_raw.empty:
        # Filtros Superiores
        c1, c2 = st.columns([1, 2])
        with c1:
            lista_cuentas = ["Todas"] + sorted(df_inv_raw['Cuenta'].unique().tolist()) if 'Cuenta' in df_inv_raw.columns else ["Todas"]
            cuenta_sel = st.selectbox("Filtrar por Cuenta:", lista_cuentas, key="inv_cuenta")
        with c2:
            busqueda = st.text_input("🔍 Buscar SKU / Lote / Ubicación:", key="inv_search")

        # Lógica de filtrado
        df_filtrado = df_inv_raw.copy()
        if cuenta_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Cuenta'] == cuenta_sel]
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

        # Cálculos para Jarra
        total_sel = df_filtrado['Cantidad'].sum()
        total_global = df_inv_raw['Cantidad'].sum()
        porcentaje = (total_sel / total_global * 100) if total_global > 0 else 0
        wave_top = 100 - max(min(porcentaje, 95), 5)

        # Renderizar Jarra
        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">PIEZAS EN {cuenta_sel.upper()}</p>
                    <h1>{total_sel:,.0f}</h1>
                </div>
                <div class="water-sphere">
                    <div class="water-percentage">{porcentaje:.1f}%</div>
                    <div class="wave wave-back" style="--wave-top: {wave_top}%;"></div>
                    <div class="wave" style="--wave-top: {wave_top}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.error("No se detectaron datos en la hoja de Inventario.")

# --- 7. SECCIÓN 2: MOVIMIENTOS ---
elif seccion == "📅 Movimientos":
    st.header("Historial de Entradas y Salidas")
    t1, t2 = st.tabs(["📥 Entradas Recientes", "📤 Salidas Recientes"])
    
    with t1:
        if not df_ent_raw.empty:
            st.dataframe(df_ent_raw, use_container_width=True)
        else: st.info("Sin registros de entradas.")
        
    with t2:
        if not df_sal_raw.empty:
            st.dataframe(df_sal_raw, use_container_width=True)
        else: st.info("Sin registros de salidas.")

# --- 8. SECCIÓN 3: SURTIDO RÁPIDO (MACRO PICKING) ---
elif seccion == "⚡ Surtido Rápido":
    st.header("Pickeador Automático por Lotes")
    st.write("Ingresa un SKU y el sistema te dirá de dónde sacarlo respetando el stock.")
    
    with st.expander("📝 Registrar Pedido", expanded=True):
        c1, c2 = st.columns(2)
        sku_p = c1.text_input("SKU solicitado:")
        cant_p = c2.number_input("Cantidad total:", min_value=1, step=1)
        
        if st.button("Generar Hoja de Picking", use_container_width=True):
            if sku_p and cant_p:
                res_df, pendiente = motor_surtido(df_inv_raw, sku_p, cant_p)
                
                if not res_df.empty:
                    st.success(f"Distribución calculada para {sku_p}")
                    st.table(res_df) # Tabla estática clara
                    if pendiente > 0:
                        st.warning(f"⚠️ Faltaron {pendiente} unidades por surtir (Stock insuficiente).")
                else:
                    st.error("No se encontró stock para este SKU.")
            else:
                st.warning("Por favor ingresa SKU y cantidad.")

# --- 9. PIE DE PÁGINA ---
st.markdown("---")
st.caption("WMS Sonda v2.0 | Conectado a Google Cloud")