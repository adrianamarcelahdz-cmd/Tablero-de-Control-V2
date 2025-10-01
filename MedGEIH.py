# -------------------------------------------------------------
# GEIH CTI Medellin — Dashboard CASOS LABORATORIO & ACTUACIONES DE CAMPO
# Ejecuta:  streamlit run app.py
# Requisitos: streamlit, pandas, plotly, numpy
# -------------------------------------------------------------

import os
import re
import unicodedata
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------
# Configuración de página
# ----------------------------
st.set_page_config(
    page_title="GEIH CTI Medellin",
    page_icon="📊",
    layout="wide",
)
st.title("📊 GEIH CTI Medellin — Casos de Laboratorio & Actuaciones de Campo")

# ----------------------------
# Rutas/URLs fuente (por defecto)
# ----------------------------
url_lab = "https://github.com/adrianamarcelahdz-cmd/Tablero-de-Control-V2/raw/refs/heads/main/Labmedellin5.csv"
url_exh = "https://github.com/adrianamarcelahdz-cmd/Tablero-de-Control-V2/raw/refs/heads/main/exhmed.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ----------------------------
# Utilidades generales
# ----------------------------
def strip_accents(s: str) -> str:
    """Elimina tildes/diacríticos sin dependencias externas."""
    if s is None:
        return ""
    nfkd = unicodedata.normalize("NFD", str(s))
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def norm_text(x) -> str:
    """
    Normaliza texto (acentos, espacios, mayúsculas).
    Blindado para no romper si llega una Serie por error.
    """
    if isinstance(x, pd.Series):
        # Usa el primer valor no nulo si llega una Serie
        for v in x:
            if not pd.isna(v):
                x = v
                break
        else:
            return ""
    if pd.isna(x):
        return ""
    s = strip_accents(str(x).strip())
    s = re.sub(r"\s+", " ", s)
    return s.upper()

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    new_cols = {}
    for c in df.columns:
        base = strip_accents(str(c)).strip().upper()
        base = re.sub(r"\s+", " ", base)
        new_cols[c] = base
    return df.rename(columns=new_cols)

# Mapeo de sinónimos -> nombre estándar esperado
COLUMN_MAP: Dict[str, str] = {
    # Laboratorio
    "CASO LIMS": "CASO LIMS",
    "CASO": "CASO LIMS",
    "NOMBRE OCCISO": "NOMBRE OCCISO",
    "MUNICIPIO DE EXHUMACION": "MUNICIPIO EXHUMACION",
    "MUNICIPIO DE EXHUMACIÓN": "MUNICIPIO EXHUMACION",
    "MUNICIPIO EXHUMACION": "MUNICIPIO EXHUMACION",
    "ANTROPOLOGO": "ANTROPOLOGO",
    "ANTROPÓLOGO": "ANTROPOLOGO",
    "MEDICO": "MEDICO",
    "ODONTOLOGO": "ODONTOLOGO",
    "ODONTÓLOGO": "ODONTOLOGO",
    "SIRDEC": "SIRDEC",
    "ESTADO": "ESTADO",
    "LEY": "LEY",
    "ANALIZADOS": "ANALIZADOS",
    "ENTREGADOS": "ENTREGADOS",
    # Campo
    "ASUNTO DE LA DILIGENCIA": "ASUNTO DE LA DILIGENCIA",
    "CUERPOS": "CUERPOS",
    "ANIO": "AÑO",
    "ANO": "AÑO",
    "AÑO": "AÑO",
    "TIPO INHUMACION": "TIPO INHUMACION",
    "TIPO INHUMACIÓN": "TIPO INHUMACION",
    "ZONA": "ZONA",
    "MUNICIPIO DE LA DILIGENCIA": "MUNICIPIO DE LA DILIGENCIA",
    "DEPARTAMENTO": "DEPARTAMENTO",
}

LAB_PREVIEW_COLS = [
    "CASO LIMS",
    "NOMBRE OCCISO",
    "MUNICIPIO EXHUMACION",
    "ANTROPOLOGO",
    "MEDICO",
    "ODONTOLOGO",
    "SIRDEC",
]

def standardize_and_remap(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    remapped = {col: COLUMN_MAP.get(col, col) for col in df.columns}
    return df.rename(columns=remapped)

def ensure_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df

def filter_by_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query:
        return df
    query_norm = norm_text(query)
    mask = pd.Series(False, index=df.index)
    # incluir 'object' y 'string' (pandas dtype moderno)
    for c in df.select_dtypes(include=["object", "string"]).columns:
        mask |= df[c].astype(str).apply(norm_text).str.contains(query_norm, na=False)
    return df[mask]

def download_button_csv(df: pd.DataFrame, label: str, filename: str):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")

# ----------------------------
# Carga robusta desde URL o ruta
# ----------------------------
@st.cache_data(show_spinner=False)
def cargar_csv(src: str) -> pd.DataFrame:
    """
    Carga CSV desde:
      - URL http(s)
      - ruta absoluta o relativa
      - 'data/<src>' si es relativa y existe
    Intenta (utf-8, latin-1) x (sep=';', sep=',').
    Devuelve DF vacío si falla.
    """
    if not src:
        return pd.DataFrame()

    def try_read(read_src: str):
        for enc in ("utf-8", "latin-1"):
            for sep in (";", ","):
                try:
                    return pd.read_csv(read_src, encoding=enc, sep=sep)
                except Exception:
                    pass
        return None

    # 1) URL
    if src.startswith("http://") or src.startswith("https://"):
        df = try_read(src)
        if df is not None:
            return df
        st.warning(f"No se pudo leer la URL: {src}")
        return pd.DataFrame()

    # 2) Ruta local tal cual o dentro de /data
    candidates = []
    if os.path.isabs(src) or os.path.exists(src):
        candidates.append(src)
    if not os.path.isabs(src):
        candidates.append(os.path.join(DATA_DIR, src))

    for path in candidates:
        if os.path.exists(path):
            df = try_read(path)
            if df is not None:
                ret
