
# GEIH5_fixed.py
# Streamlit dashboard: CASOS LABORATORIO & ACTUACIONES DE CAMPO
# Run with: streamlit run GEIH5_fixed.py
# Requires: pip install streamlit pandas plotly unidecode

import streamlit as st
import pandas as pd
import plotly.express as px
from unidecode import unidecode
import re

st.set_page_config(page_title="Tablero de Control V2", page_icon="🧭", layout="wide")

# ------------------------ Utils ------------------------
@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
        return df
    except Exception:
        # Fallback common encodings
        for enc in ("utf-8-sig", "latin1", "cp1252"):
            try:
                return pd.read_csv(url, encoding=enc)
            except Exception:
                continue
    return pd.DataFrame()

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: strip, upper, remove accents, collapse spaces."""
    df = df.copy()
    mapping = {}
    for c in df.columns:
        cc = unidecode(str(c)).upper().strip()
        cc = re.sub(r"\s+", " ", cc)
        mapping[c] = cc
    df.rename(columns=mapping, inplace=True)
    return df

def get_col(df: pd.DataFrame, candidates):
    """Return first matching column by normalized name from candidates (list of strings)."""
    if df.empty:
        return None
    norm = {unidecode(c).upper().strip(): c for c in df.columns}
    for cand in candidates:
        key = unidecode(cand).upper().strip()
        if key in norm:
            return norm[key]
    # Partial contains match
    for key, original in norm.items():
        for cand in candidates:
            if key.find(unidecode(cand).upper().strip()) != -1:
                return original
    return None

def to_top10(s: pd.Series) -> pd.Series:
    vc = s.fillna("SIN DATO").astype(str).value_counts()
    return vc.head(10)

# ------------------------ Data ------------------------
URL_LAB = "https://github.com/adrianamarcelahdz-cmd/Tablero-de-Control-V2/raw/refs/heads/main/Labmedellin5.csv"
URL_EXH = "https://github.com/adrianamarcelahdz-cmd/Tablero-de-Control-V2/raw/refs/heads/main/exhmed.csv"

lab = load_csv(URL_LAB)
exh = load_csv(URL_EXH)

lab = norm_cols(lab)
exh = norm_cols(exh)

# Likely column names (normalized, without accents)
COL_CASO_LIMS = get_col(lab, ["CASO LIMS", "CASO_LIMS", "CASO", "CASO LIMS ID"])
COL_NOMBRE = get_col(lab, ["NOMBRE OCCISO", "NOMBRE DEL OCCISO", "NOMBRE"])
COL_MUNI_EXH = get_col(lab, ["MUNICIPIO DE EXHUMACION", "MUNICIPIO EXHUMACION", "MUNICIPIO DE EXHUMACIÓN"])
COL_ANTRO = get_col(lab, ["ANTROPOLOGO", "ANTROPOLOGO(A)", "ANTROPOLOGA", "ANTROPOLOGO RESPONSABLE"])
COL_MED = get_col(lab, ["MEDICO", "MEDICO(A)", "MEDICA"])
COL_ODON = get_col(lab, ["ODONTOLOGO", "ODONTOLOGO(A)", "ODONTOLOGA"])
COL_SIRDEC = get_col(lab, ["SIRDEC"])
COL_ESTADO = get_col(lab, ["ESTADO"])
COL_LEY = get_col(lab, ["LEY"])

# Possible delivered indicator columns (best effort)
COL_ENTREGADO = get_col(lab, ["ENTREGADO", "ENTREGADOS", "ENTREGA", "ENTREGAS"])

# EXH columns
COL_ASUNTO = get_col(exh, ["ASUNTO DE LA DILIGENCIA", "ASUNTO", "ASUNTO DILIGENCIA"])
COL_CUERPOS = get_col(exh, ["CUERPOS", "CANTIDAD DE CUERPOS", "NO. CUERPOS", "NRO CUERPOS"])
COL_ANIO = get_col(exh, ["AÑO", "ANO", "ANIO", "ANNO", "ANIO DILIGENCIA"])
COL_TIPO_INH = get_col(exh, ["TIPO INHUMACION", "TIPO DE INHUMACION", "TIPO_INHUMACION"])
COL_ZONA = get_col(exh, ["ZONA", "ZONA DE LA DILIGENCIA"])
COL_MUNI_DIL = get_col(exh, ["MUNICIPIO DE LA DILIGENCIA", "MUNICIPIO", "MUNICIPIO DILIGENCIA"])
COL_DEPTO = get_col(exh, ["DEPARTAMENTO", "DEPTO", "DEPARTAMENTO DE LA DILIGENCIA"])

st.title("🧭 Tablero de Control V2")

tabs = st.tabs(["CASOS LABORATORIO", "ACTUACIONES DE CAMPO"])

# ======================== Tab 1: CASOS LABORATORIO ========================
with tabs[0]:
    st.subheader("CASOS LABORATORIO")

    if lab.empty:
        st.warning("No se pudo cargar Labmedellin5.csv desde la URL indicada.")
    else:
        # ---- Tarjetas CIH/GEIH vs GIH ----
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            if COL_CASO_LIMS:
                serie = lab[COL_CASO_LIMS].astype(str).str.upper()
                count_cih = serie.str.contains("CIH", na=False).sum() + serie.str.contains("GEIH", na=False).sum()
                st.metric("CIH", value=int(count_cih))
            else:
                st.metric("CIH", value="N/D")
        with col2:
            if COL_CASO_LIMS:
                serie = lab[COL_CASO_LIMS].astype(str).str.upper()
                count_gih = serie.str.contains("GIH", na=False).sum()
                st.metric("BUNKER (GIH)", value=int(count_gih))
            else:
                st.metric("BUNKER (GIH)", value="N/D")
        with col3:
            st.caption("Conteos basados en coincidencias de texto dentro de la columna CASO LIMS (CIH, GEIH y GIH).")

        st.divider()

        # ---- Previsualización de tabla ----
        st.markdown("#### Previsualización de casos")
        desired_cols = [COL_CASO_LIMS, COL_NOMBRE, COL_MUNI_EXH, COL_ANTRO, COL_MED, COL_ODON, COL_SIRDEC]
        show_cols = [c for c in desired_cols if c in lab.columns and c is not None]
        if len(show_cols) == 0:
            st.info("No se encontraron las columnas solicitadas en el archivo. Se muestran las primeras columnas disponibles.")
            st.dataframe(lab.head(50))
        else:
            st.dataframe(lab[show_cols].head(100))

        st.divider()

        # ---- Tarjetas de ESTADO ----
        st.markdown("#### Estado de laboratorio")
        estados_principales = ["ANALIZADO", "PENDIENTE", "PERFILADO", "POSITIVO", "NEGATIVO"]
        otros_estados = {"REMITIDOS", "GENETICA", "NO PERFILO", "CANCELADO", "ND"}
        if COL_ESTADO:
            estado_ser = lab[COL_ESTADO].fillna("SIN DATO").astype(str).str.upper().str.strip()
            cols = st.columns(len(estados_principales) + 1)
            for i, est in enumerate(estados_principales):
                cols[i].metric(est.title(), int((estado_ser == est).sum()))
            mask_otros = estado_ser.isin(otros_estados)
            cols[-1].metric("OTROS ESTADOS", int(mask_otros.sum()))
        else:
            st.info("No se encontró la columna ESTADO en el archivo.")

        st.divider()

        # ---- Gráfico de barras por LEY ----
        st.markdown("#### Distribución por LEY")
        if COL_LEY:
            ley_series = lab[COL_LEY].fillna("SIN DATO").astype(str)
            df_ley = ley_series.value_counts().reset_index(name="CANTIDAD").rename(columns={"index": "LEY"})
            fig = px.bar(
                df_ley, x="LEY", y="CANTIDAD",
                labels={"LEY":"LEY", "CANTIDAD":"CANTIDAD"},
                title="Casos por LEY"
            )
            fig.update_layout(xaxis_tickangle=-45, height=420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontró la columna LEY.")

        st.divider()

        # ---- Top 10 municipios vs Analizados/Entregados ----
        st.markdown("#### Top 10 Municipios de Exhumación: Analizados vs Entregados")
        if COL_MUNI_EXH:
            muni_all = lab[COL_MUNI_EXH].fillna("SIN DATO").astype(str).str.upper().str.strip()
            top10 = to_top10(muni_all).index.tolist()
            df_top = lab[muni_all.isin(top10)].copy()

            # Flags
            analyzed_flag = None
            if COL_ESTADO:
                analyzed_flag = df_top[COL_ESTADO].fillna("").astype(str).str.upper().str.contains(r"\bANALIZADO\b")

            delivered_flag = None
            if COL_ENTREGADO and COL_ENTREGADO in df_top.columns:
                delivered_flag = df_top[COL_ENTREGADO].fillna("").astype(str).str.upper().str.contains("SI|ENTREG")
            elif COL_SIRDEC and COL_SIRDEC in df_top.columns:
                delivered_flag = df_top[COL_SIRDEC].fillna("").astype(str).str.upper().str.contains("ENTREG")

            df_top["_MUNICIPIO_"] = muni_all[muni_all.isin(top10)]
            agg = []
            for m in top10:
                sub = df_top[df_top["_MUNICIPIO_"] == m]
                anal = int(analyzed_flag[sub.index].sum()) if analyzed_flag is not None else 0
                entr = int(delivered_flag[sub.index].sum()) if delivered_flag is not None else 0
                agg.append({"MUNICIPIO EXHUMACION": m, "ANALIZADOS": anal, "ENTREGADOS": entr})
            df_agg = pd.DataFrame(agg)

            df_long = df_agg.melt(id_vars="MUNICIPIO EXHUMACION", var_name="CATEGORIA", value_name="CANTIDAD")
            fig2 = px.bar(df_long, x="MUNICIPIO EXHUMACION", y="CANTIDAD", color="CATEGORIA",
                          barmode="group", title="Top 10 Municipios: Analizados vs Entregados")
            fig2.update_layout(xaxis_tickangle=-45, height=480)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No se encontró la columna de municipio de exhumación.")

# ===================== Tab 2: ACTUACIONES DE CAMPO =====================
with tabs[1]:
    st.subheader("ACTUACIONES DE CAMPO")

    if exh.empty:
        st.warning("No se pudo cargar exhmed.csv desde la URL indicada.")
    else:
        # ---- Tarjetas: ASUNTO & CUERPOS ----
        c1, c2, c3 = st.columns(3)
        with c1:
            if COL_ASUNTO:
                total_asuntos = exh[COL_ASUNTO].notna().sum()
                st.metric("ASUNTO DE LA DILIGENCIA", int(total_asuntos))
            else:
                st.metric("ASUNTO DE LA DILIGENCIA", "N/D")
        with c2:
            if COL_CUERPOS:
                total_cuerpos = pd.to_numeric(exh[COL_CUERPOS], errors="coerce").fillna(0).sum()
                st.metric("CANTIDAD DE CUERPOS", int(total_cuerpos))
            else:
                st.metric("CANTIDAD DE CUERPOS", "N/D")
        with c3:
            st.caption("Conteos directos de filas (ASUNTO) y suma numérica de CUERPOS.")

        st.divider()

        # ---- Barras por AÑO agrupado en quinquenios ----
        st.markdown("#### Casos por período de 5 años")
        if COL_ANIO:
            anio = pd.to_numeric(exh[COL_ANIO], errors="coerce")
            quinquenio = (anio // 5) * 5
            labels = quinquenio.fillna(-1).astype(int).astype(str).replace({"-1":"SIN DATO"})
            df_q = labels.value_counts().sort_index().reset_index()
            df_q.columns = ["PERIODO_INICIO", "CANTIDAD"]
            df_q["PERIODO"] = df_q["PERIODO_INICIO"].apply(lambda x: "SIN DATO" if x == "SIN DATO" else f"{x}-{int(x)+4}")
            fig3 = px.bar(df_q, x="PERIODO", y="CANTIDAD", title="Distribución por quinquenios (AÑO)")
            fig3.update_layout(xaxis_tickangle=-30, height=420)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No se encontró la columna AÑO/ANIO.")

        st.divider()

        # ---- Barras TIPO INHUMACION (porcentaje) ----
        st.markdown("#### Tipo de inhumación (porcentaje)")
        if COL_TIPO_INH:
            tipo = exh[COL_TIPO_INH].fillna("SIN DATO").astype(str).str.upper().str.strip()
            vc = tipo.value_counts()
            df_tipo = (vc / vc.sum() * 100).reset_index()
            df_tipo.columns = ["TIPO INHUMACION", "PORCENTAJE"]
            fig4 = px.bar(df_tipo, x="TIPO INHUMACION", y="PORCENTAJE",
                          title="TIPO INHUMACION (%).")
            fig4.update_layout(xaxis_tickangle=-45, height=420, yaxis_ticksuffix="%")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No se encontró la columna TIPO INHUMACION.")

        st.divider()

        # ---- Pie chart ZONA con agrupación ----
        st.markdown("#### ZONA (agrupada)")
        if COL_ZONA:
            zona = exh[COL_ZONA].fillna("SIN DATO").astype(str).str.upper().str.strip()
            zona = zona.replace({
                "ZONA RURAL":"RURAL",
                "RURAL":"RURAL",
                "URBANO":"URBANA",
                "URBANA":"URBANA",
                "CEMENTERIO":"CEMENTERIO"
            })
            fig5 = px.pie(zona.value_counts().reset_index(name="CANTIDAD").rename(columns={"index":"ZONA"}),
                          names="ZONA", values="CANTIDAD",
                          title="Distribución por ZONA (agrupada)")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No se encontró la columna ZONA.")

        st.divider()

        # ---- Mapa de calor Municipio vs Departamento ----
        st.markdown("#### Mapa de calor: Municipio vs Departamento")
        if COL_MUNI_DIL and COL_DEPTO:
            muni = exh[COL_MUNI_DIL].fillna("SIN DATO").astype(str).str.upper().str.strip()
            depto = exh[COL_DEPTO].fillna("SIN DATO").astype(str).str.upper().str.strip()
            piv = pd.crosstab(muni, depto)
            fig6 = px.imshow(piv, aspect="auto", title="Heatmap MUNICIPIO DE LA DILIGENCIA x DEPARTAMENTO",
                             labels=dict(x="DEPARTAMENTO", y="MUNICIPIO", color="CANTIDAD"))
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No se encontraron las columnas MUNICIPIO DE LA DILIGENCIA y/o DEPARTAMENTO.")
