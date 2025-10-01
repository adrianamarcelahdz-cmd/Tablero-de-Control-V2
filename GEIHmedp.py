# app.py
# Dashboard Forense Streamlit - Multi Pestaña
# Ejecutar con: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import unidecode
from typing import List

st.set_page_config(page_title="Dashboard Forense", layout="wide")

# =========================
# Utilidades y Normalización
# =========================

import os

@st.cache_data
def cargar_csv(path):
    """Carga un CSV intentando primero la ruta dada y luego en 'data/'. Devuelve DataFrame vacío si no existe."""
    # Intenta ruta directa
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding='latin-1')
        except Exception:
            pass
    # Intenta en carpeta data/
    data_path = os.path.join('data', path)
    if os.path.exists(data_path):
        try:
            return pd.read_csv(data_path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(data_path, encoding='latin-1')
        except Exception:
            pass
    # Si no existe, devuelve DataFrame vacío y muestra advertencia
    st.warning(f"No se encontró el archivo '{path}' ni en 'data/{path}'.")
    return pd.DataFrame()

def normalizar_cols(df, mapeo):
    """Estripa, mayusculiza y elimina tildes de columnas. Renombra usando mapeo."""
    nuevo_cols = []
    for col in df.columns:
        clean = unidecode.unidecode(col.strip().upper())
        clean = mapeo.get(clean, clean)
        nuevo_cols.append(clean)
    df.columns = nuevo_cols
    return df

def safe_column(df, nombre, fill=None):
    if nombre not in df.columns:
        df[nombre] = fill
    return df

def periodizar_anios(df, col='AÑO'):
    if col in df.columns:
        miny = int(df[col].min())
        maxy = int(df[col].max())
        bins = list(range((miny//5)*5, ((maxy//5)+2)*5, 5))
        labels = [f"{b}-{b+4}" for b in bins[:-1]]
        df['PERIODO_5'] = pd.cut(df[col], bins=bins, labels=labels, right=True, include_lowest=True)
    else:
        df['PERIODO_5'] = "No especificado"
    return df

def agrupar_zona(z):
    if pd.isna(z): return "No especificado"
    z = z.upper()
    if z in ['RURAL', 'ZONA RURAL']:
        return "RURAL"
    elif z in ['URBANA', 'URBANO']:
        return "URBANA"
    return "OTRAS"

def contar_estado(df, estados: List[str], col='ESTADO'):
    if col not in df.columns: return 0
    return df[df[col].str.upper().isin([e.upper() for e in estados])].shape[0]

# ==============
# Diccionario Mapeos
# ==============
MAPEO_COLS = {
    "CASO LIMS":"CASO LIMS",
    "NOMBRE OCCISO":"NOMBRE OCCISO",
    "MUNICIPIO DE EXHUMACION": "MUNICIPIO DE EXHUMACIÓN",
    "MUNICIPIO DE EXHUMACIÓN": "MUNICIPIO DE EXHUMACIÓN",
    "ANTROPOLOGO":"ANTROPOLOGO",
    "MEDICO":"MEDICO",
    "ODONTOLOGO":"ODONTOLOGO",
    "SIRDEC":"SIRDEC",
    "ESTADO":"ESTADO",
    "LEY": "LEY",
    "ENTREGADOS": "ENTREGADOS",
    "ANALIZADOS": "ANALIZADOS",
    "ASUNTO DE LA DILIGENCIA": "ASUNTO DE LA DILIGENCIA",
    "CUERPOS": "CUERPOS",
    "AÑO": "AÑO",
    "TIPO INHUMACION": "TIPO INHUMACION",
    "ZONA": "ZONA",
    "MUNICIPIO DE LA DILIGENCIA": "MUNICIPIO DE LA DILIGENCIA",
    "DEPARTAMENTO": "DEPARTAMENTO"
}

# =========================
# Sidebar: Filtros globales
# =========================
def filtros_sidebar(df1, df2):
    st.sidebar.header("Filtros globales")
    # Año, departamento, búsqueda texto
    anios = []
    if "AÑO" in df1.columns:
        anios += list(df1["AÑO"].dropna().unique())
    if "AÑO" in df2.columns:
        anios += list(df2["AÑO"].dropna().unique())
    # Solo valores numéricos válidos
    anios_validos = []
    for y in anios:
        try:
            val = int(y)
            anios_validos.append(val)
        except (ValueError, TypeError):
            continue
    anios_validos = sorted(set(anios_validos))
    anio = st.sidebar.selectbox("Año", options=["Todos"]+anios_validos, index=0)

    depts = []
    if "DEPARTAMENTO" in df1.columns: depts += list(df1["DEPARTAMENTO"].dropna().unique())
    if "DEPARTAMENTO" in df2.columns: depts += list(df2["DEPARTAMENTO"].dropna().unique())
    depts = sorted([d for d in set(depts) if pd.notna(d)])
    dept = st.sidebar.selectbox("Departamento", options=["Todos"]+depts, index=0)

    q = st.sidebar.text_input("Buscar texto...")

    return anio, dept, q

# =========================
# Data Preparation
# =========================
# Cargar y limpiar
df_lab = normalizar_cols(cargar_csv('Labmedellin5.csv'), MAPEO_COLS)
df_campo = normalizar_cols(cargar_csv('exhmed.csv'), MAPEO_COLS)

# Completa columnas que pueden faltar
for col in ["CASO LIMS","NOMBRE OCCISO","MUNICIPIO DE EXHUMACIÓN","ANTROPOLOGO","MEDICO","ODONTOLOGO","SIRDEC"]:
    df_lab = safe_column(df_lab, col, fill="No especificado")

for col in ["ASUNTO DE LA DILIGENCIA", "CUERPOS", "AÑO","TIPO INHUMACION","ZONA","MUNICIPIO DE LA DILIGENCIA","DEPARTAMENTO"]:
    df_campo = safe_column(df_campo, col, fill="No especificado")

df_campo["CUERPOS"] = pd.to_numeric(df_campo["CUERPOS"], errors='coerce').fillna(0).astype(int)
df_lab = safe_column(df_lab, "ENTREGADOS", fill=0)
df_lab = safe_column(df_lab, "ANALIZADOS", fill=0)
if "ESTADO" in df_lab.columns:
    df_lab["ANALIZADOS"] = df_lab["ESTADO"].str.upper().eq("ANALIZADO").astype(int)
    df_lab["ENTREGADOS"] = df_lab["ESTADO"].str.upper().eq("ENTREGADO").astype(int)

# Filtros globales
anio, dept, query = filtros_sidebar(df_lab, df_campo)

def aplicar_filtros(df):
    tmp = df.copy()
    if anio != "Todos" and "AÑO" in tmp.columns:
        tmp = tmp[tmp["AÑO"]==anio]
    if dept != "Todos" and "DEPARTAMENTO" in tmp.columns:
        tmp = tmp[tmp["DEPARTAMENTO"]==dept]
    if query:
        mask = tmp.apply(lambda x: x.astype(str).str.contains(query, case=False, na=False)).any(axis=1)
        tmp = tmp[mask]
    return tmp

# =========================
# App principal (Tabs)
# =========================

tab1, tab2 = st.tabs(["CASOS LABORATORIO", "ACTUACIONES DE CAMPO"])

with tab1:
    dfl = aplicar_filtros(df_lab)
    st.subheader("Panel de Casos Laboratorio")

    # ---- 1. Tarjetas CIH/BUNKER ----
    cih_count = dfl["CASO LIMS"].str.upper().fillna("").str.contains("CIH|GEIH").sum()
    bunker_count = dfl["CASO LIMS"].str.upper().fillna("").str.contains("GIH").sum()
    total = len(dfl)

    cih_pct = (cih_count/total*100) if total else 0
    bunker_pct = (bunker_count/total*100) if total else 0

    col1, col2 = st.columns(2)
    col1.metric("CIH/GEIH", f"{cih_count}", f"{cih_pct:.1f}% del total")
    col2.metric("BUNKER (GIH)", f"{bunker_count}", f"{bunker_pct:.1f}% del total")

    # ---- 2. Tabla previsualización ----
    st.markdown("### Previsualización de registros")
    preview_cols = ["CASO LIMS","NOMBRE OCCISO","MUNICIPIO DE EXHUMACIÓN","ANTROPOLOGO","MEDICO","ODONTOLOGO","SIRDEC"]
    missing = [c for c in preview_cols if c not in dfl.columns]
    for c in missing:
        dfl[c] = "No especificado"
    num_rows = st.selectbox("Filas a mostrar", [10,25,50,100], index=0)
    search_table = st.text_input("Buscar en la tabla...")
    tdf = dfl[preview_cols]
    if search_table:
        mask = tdf.apply(lambda x: x.astype(str).str.contains(search_table, case=False, na=False)).any(axis=1)
        tdf = tdf[mask]
    st.dataframe(tdf.head(num_rows))

    # ---- 3. Tarjetas Estado ----
    st.markdown("### Estado de los casos")
    estados_principales = ["ANALIZADO", "PENDIENTE", "PERFILADO", "POSITIVO", "NEGATIVO"]
    otros_estados = ["REMITIDOS", "GENETICA", "NO PERFILO", "CANCELADO", "ND"]
    cols = st.columns(len(estados_principales)+1)
    suma_total = len(dfl)
    for i, estado in enumerate(estados_principales):
        c = dfl["ESTADO"].str.upper().eq(estado).sum()
        pct = (c/suma_total)*100 if suma_total else 0
        cols[i].metric(estado, c, f"{pct:.1f}%")
    otros = dfl["ESTADO"].str.upper().isin([x.upper() for x in otros_estados]).sum()
    pct_otros = (otros/suma_total)*100 if suma_total else 0
    cols[-1].metric("OTROS ESTADOS", otros, f"{pct_otros:.1f}%")

    # ---- 4. Gráfico barras por LEY ----
    st.markdown("### Casos por Ley")
    if "LEY" in dfl.columns:
        ley_plot = dfl["LEY"].value_counts().reset_index()
        ley_plot.columns = ["LEY", "count"]
        fig_ley = px.bar(ley_plot, x="LEY", y="count", labels={"LEY":"LEY","count":"Cantidad"}, text="count")
        fig_ley.update_traces(textposition="outside")
        fig_ley.update_layout(xaxis_title="LEY", yaxis_title="Cantidad")
        st.plotly_chart(fig_ley, use_container_width=True)

    # ---- 5. Top 10 municipios ----
    st.markdown("### Top 10 Municipios (Analizados vs Entregados)")
    if "MUNICIPIO DE EXHUMACIÓN" in dfl.columns:
        muni_plot = dfl.groupby("MUNICIPIO DE EXHUMACIÓN").agg({
            "ANALIZADOS": "sum",
            "ENTREGADOS": "sum"
        }).reset_index()
        top10 = muni_plot.sort_values('ANALIZADOS', ascending=False).head(10)
        fig_muni = go.Figure(data=[
            go.Bar(name='Analizados', x=top10["MUNICIPIO DE EXHUMACIÓN"], y=top10["ANALIZADOS"], text=top10["ANALIZADOS"], textposition='outside'),
            go.Bar(name='Entregados', x=top10["MUNICIPIO DE EXHUMACIÓN"], y=top10["ENTREGADOS"], text=top10["ENTREGADOS"], textposition='outside')
        ])
        fig_muni.update_layout(barmode='group', xaxis_title="Municipio", yaxis_title="Casos", legend_title="Tipo")
        st.plotly_chart(fig_muni, use_container_width=True)

    # ---- 6. Descarga CSV ----
    csv = dfl.to_csv(index=False).encode()
    st.download_button("Descargar datos filtrados (CSV)", csv, "casos_lab_filtrado.csv", "text/csv")

with tab2:
    dfc = aplicar_filtros(df_campo)
    st.subheader("Panel de Actuaciones de Campo")
    # ---- 1. Tarjetas ----
    total_asunto = len(dfc)
    most_common = dfc["ASUNTO DE LA DILIGENCIA"].mode().iloc[0] if not dfc["ASUNTO DE LA DILIGENCIA"].isna().all() else "No especificado"
    total_cuerpos = dfc["CUERPOS"].sum()
    col1, col2 = st.columns(2)
    col1.metric("Total registros (Asunto de la Diligencia)", total_asunto, f"Frecuente: {most_common}")
    col2.metric("Cantidad de Cuerpos", total_cuerpos)

    # ---- 2. Barras por AÑO en periodos de 5 ----
    dfc = periodizar_anios(dfc, 'AÑO')
    st.markdown("### Casos por periodo de 5 años")
    if "PERIODO_5" in dfc.columns:
        per5 = dfc["PERIODO_5"].value_counts().sort_index().reset_index()
        fig_p = px.bar(per5, x="index", y="PERIODO_5", labels={"index":"Periodo (5 años)", "PERIODO_5":"Cantidad"}, text="PERIODO_5")
        fig_p.update_traces(textposition="outside")
        fig_p.update_layout(xaxis_title="Periodo", yaxis_title="Casos")
        st.plotly_chart(fig_p, use_container_width=True)

    # ---- 3. Barras por Tipo Inhumación (%) ----
    st.markdown("### Tipos de Inhumación (%)")
    if "TIPO INHUMACION" in dfc.columns:
        tipo_plot = dfc["TIPO INHUMACION"].value_counts(normalize=True).mul(100).round(1).reset_index().rename(columns={"TIPO INHUMACION":"%","index":"TIPO"})
        fig_tipo = px.bar(tipo_plot, y="TIPO", x="%", orientation="h", text="%", labels={"TIPO":"Tipo de Inhumación","%":"Porcentaje"})
        fig_tipo.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Porcentaje")
        st.plotly_chart(fig_tipo, use_container_width=True)

    # ---- 4. Pie chart por ZONA ----
    st.markdown("### Distribución por Zona")
    dfc["ZONA_NORMAL"] = dfc["ZONA"].apply(agrupar_zona)
    zona_plot = dfc["ZONA_NORMAL"].value_counts(normalize=True).mul(100).round(1).reset_index().rename(columns={"index":"ZONA","ZONA_NORMAL":"%"})
    fig_z = px.pie(zona_plot, values="%", names="ZONA", title="Zona", hole=0.3)
    fig_z.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_z, use_container_width=True)

    # ---- 5. Heatmap municipio vs departamento ----
    st.markdown("### Mapa de calor: Municipio vs Departamento")
    pc = pd.pivot_table(dfc, index="DEPARTAMENTO", columns="MUNICIPIO DE LA DILIGENCIA", aggfunc="size", fill_value=0)
    fig_hm = go.Figure(data=go.Heatmap(
        z=pc.values,
        x=pc.columns,
        y=pc.index,
        colorscale='Blues',
        hoverongaps=False,
        colorbar_title="N° de Registros",
        text=pc.values,
        texttemplate="%{text}"
    ))
    fig_hm.update_layout(xaxis_title="Municipio", yaxis_title="Departamento", title="Heatmap Departamento vs Municipio")
    st.plotly_chart(fig_hm, use_container_width=True)

    # ---- 6. Descarga CSV ----
    csv2 = dfc.to_csv(index=False).encode()
    st.download_button("Descargar datos filtrados (CSV)", csv2, "actuaciones_campo_filtrado.csv", "text/csv")
