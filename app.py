import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="WMS Sonda Pro", layout="wide")

# ==========================================
# 🔗 ENLACES DE GOOGLE SHEETS (CSV EXPORT)
# ==========================================
URL_INVENTARIO = "https://docs.google.com/spreadsheets/d/135jZiPzcgSz64NYybCYa8PIu8LAoyjk5IIn6NrEHjZ4/export?format=csv"
URL_ENTRADAS = "https://docs.google.com/spreadsheets/d/1mczk_zLZqypIXJY6uQqFj_5ioLHybasecxgNKzlopwc/export?format=csv"
URL_SALIDAS = "https://docs.google.com/spreadsheets/d/1aB-ODOa6-npqxX_WmWTOQuxYoWE1KxVAGNoSOcYoFck/export?format=csv" 

# --- 2. ESTILOS CSS REFINADOS ---
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }
    
    .kpi-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 60px;
        background: #ffffff;
        border-radius: 25px;
        padding: 40px;
        margin-bottom: 30px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .kpi-text-box h1 { 
        font-size: 5rem !important; 
        color: #0f172a !important; 
        margin: 0; 
        font-weight: 800 !important;
        letter-spacing: -3px;
        line-height: 0.8;
    }

    .label-kpi {
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 0.85rem;
    }

    .water-sphere {
        width: 170px;
        height: 170px;
        background-color: #f8fafc;
        border-radius: 50%;
        position: relative;
        overflow: hidden;
        border: 2px solid #f1f5f9;
    }

    .wave {
        position: absolute;
        bottom: 0;
        left: -50%;
        width: 200%;
        height: 200%;
        background: rgba(2, 132, 199, 0.8);
        border-radius: 40%;
        animation: wave-animation 6s infinite linear;
        top: var(--wave-top);
        z-index: 2;
        transition: top 1s ease-in-out;
    }

    .wave-back {
        background: rgba(125, 211, 252, 0.4);
        animation: wave-animation 9s infinite linear;
        z-index: 1;
        top: calc(var(--wave-top) - 5%);
    }

    @keyframes wave-animation {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .water-percentage {
        position: absolute;
        width: 100%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        color: #1e293b;
        font-weight: 800;
        font-size: 1.5rem;
        z-index: 10;
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
            # Limpieza de datos numéricos
            if 'Cantidad' in df.columns:
                df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error cargando {url}: {e}")
            return pd.DataFrame()
    return fetch(URL_INVENTARIO), fetch(URL_ENTRADAS), fetch(URL_SALIDAS)

df_inv_raw, df_ent_raw, df_sal_raw = cargar_datos()

# --- 4. LÓGICA DE DISTRIBUCIÓN (SIMULACIÓN DE LA MACRO) ---
def procesar_distribucion(df_inventario, sku_buscado, cantidad_pedida):
    """Réplica de la macro de Excel para distribuir stock por lotes y ubicaciones"""
    inv = df_inventario[df_inventario['SKU'] == sku_buscado].copy()
    asignaciones = []
    restante = cantidad_pedida
    
    for idx, row in inv.iterrows():
        if restante <= 0: break
        if row['Cantidad'] > 0:
            tomar = min(row['Cantidad'], restante)
            asignaciones.append({
                'Lote': row['Lote'],
                'Ubicación': row['Ubicación'],
                'Cantidad Sacada': tomar
            })
            restante -= tomar
            
    return pd.DataFrame(asignaciones), restante

# --- 5. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h1 style='font-size: 1.5rem;'>📦 WMS SONDA</h1>", unsafe_allow_html=True)
    seccion = st.radio("MENÚ PRINCIPAL", ["Inventario General", "Movimientos", "Surtido Automático"])
    st.markdown("---")
    if st.button("🔄 Refrescar Base de Datos"):
        st.cache_data.clear()
        st.rerun()

# --- 6. INTERFAZ: INVENTARIO GENERAL ---
if seccion == "Inventario General":
    st.title("📋 Estado de Inventario")
    
    if not df_inv_raw.empty:
        # Filtros persistentes
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            cuentas = ["Todas"] + sorted(df_inv_raw['Cuenta'].unique().tolist())
            cuenta_sel = st.selectbox("Filtrar por Cuenta:", cuentas)
        
        with col_f2:
            busqueda = st.text_input("🔍 Buscar SKU, Lote o Ubicación:", placeholder="Escribe para filtrar...")

        # Aplicar Filtros
        df_f = df_inv_raw.copy()
        if cuenta_sel != "Todas":
            df_f = df_f[df_f['Cuenta'] == cuenta_sel]
        if busqueda:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

        # KPIs y Jarra
        total_piezas = df_f['Cantidad'].sum()
        total_total = df_inv_raw['Cantidad'].sum()
        pct = (total_piezas / total_total * 100) if total_total > 0 else 0
        w_top = 100 - max(min(pct, 95), 5)

        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-text-box">
                    <p class="label-kpi">EXISTENCIAS EN {cuenta_sel.upper()}</p>
                    <h1>{total_piezas:,.0f}</h1>
                </div>
                <div class="water-sphere">
                    <div class="water-percentage">{pct:.1f}%</div>
                    <div class="wave wave-back" style="--wave-top: {w_top}%;"></div>
                    <div class="wave" style="--wave-top: {w_top}%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(df_f, use_container_width=True, hide_index=True)
        
        # Botón de Descarga
        buf = io.BytesIO()
        df_f.to_excel(buf, index=False, engine='xlsxwriter')
        st.download_button("📥 Descargar Reporte Excel", buf.getvalue(), "Inventario.xlsx", "application/vnd.ms-excel")

# --- 7. INTERFAZ: MOVIMIENTOS (ENTRADAS/SALIDAS) ---
elif seccion == "Movimientos":
    tipo_mov = st.tabs(["📥 Entradas", "📤 Salidas"])
    
    for i, tab in enumerate(tipo_mov):
        with tab:
            df_m = df_ent_raw if i == 0 else df_sal_raw
            if not df_m.empty:
                c1, c2, c3 = st.columns([1, 1, 2])
                f_inicio = c1.date_input("Desde:", datetime.now() - timedelta(days=30), key=f"f1_{i}")
                f_fin = c2.date_input("Hasta:", datetime.now(), key=f"f2_{i}")
                
                # Filtro de fecha
                df_m = df_m[(df_m['Fecha'].dt.date >= f_inicio) & (df_m['Fecha'].dt.date <= f_fin)]
                
                st.dataframe(df_m, use_container_width=True, hide_index=True)

# --- 8. INTERFAZ: SURTIDO AUTOMÁTICO (LA "MACRO" EN WEB) ---
elif seccion == "Surtido Automático":
    st.title("⚡ Surtido Inteligente de Stock")
    st.info("Esta herramienta simula la macro de Excel: busca el SKU y te dice de qué lote y ubicación sacarlo.")
    
    col1, col2 = st.columns(2)
    sku_p = col1.text_input("Ingrese SKU a surtir:")
    cant_p = col2.number_input("Cantidad necesaria:", min_value=1, step=1)
    
    if st.button("Calcular Distribución de Picking"):
        if sku_p in df_inv_raw['SKU'].values:
            res_df, faltante = procesar_distribucion(df_inv_raw, sku_p, cant_p)
            
            if not res_df.empty:
                st.subheader("📍 Hoja de Picking Generada")
                st.table(res_df)
                if faltante > 0:
                    st.error(f"⚠️ Stock insuficiente. Faltaron {faltante} unidades por asignar.")
                else:
                    st.success("✅ Pedido cubierto totalmente con el stock existente.")
            else:
                st.error("No hay stock disponible para este SKU.")
        else:
            st.warning("El SKU ingresado no existe en el inventario.")