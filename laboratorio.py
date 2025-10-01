import streamlit as st
import pandas as pd
import difflib
from io import BytesIO
import unicodedata  # para normalizar texto

st.title("Comparar, Analizar y Unir Archivos CSV")

# ---------- Utilidades ----------
def quitar_tildes(s: str) -> str:
    if s is None:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")

def norm_caso(s: str) -> str:
    # normaliza campos de texto tipo "caso" (criterio 1)
    s = "" if s is None else str(s)
    s = s.replace("\n", " ").replace("\r", " ")
    s = " ".join(s.split()).strip().lower()
    s = quitar_tildes(s)
    return s

def norm_radicado(s: str) -> str:
    # normaliza campos tipo "radicado" (criterio 2)
    s = "" if s is None else str(s)
    return s.strip()

# ---------- Carga ----------
file_lab = st.file_uploader("Sube **Archivo laboratorio**.csv", type=['csv'])
file_exh = st.file_uploader("Sube **Exhumaciones**.csv)", type=['csv'])

df_lab = None     # antes df_lunes
df_exh = None     # antes df_martes

if file_lab:
    try:
        df_lab = pd.read_csv(file_lab, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df_lab = pd.read_csv(file_lab, encoding="latin1")
        except Exception as e:
            st.error(f"Error al leer **Archivo laboratorio**: {e}")
    except Exception as e:
        st.error(f"Error al leer **Archivo laboratorio**: {e}")

if file_exh:
    try:
        df_exh = pd.read_csv(file_exh, encoding="utf-8", on_bad_lines='skip')
    except UnicodeDecodeError:
        try:
            df_exh = pd.read_csv(file_exh, encoding="latin1", on_bad_lines='skip')
        except Exception as e:
            st.error(f"Error al leer **Exhumaciones**: {e}")
    except Exception as e:
        st.error(f"Error al leer **Exhumaciones**: {e}")

# ---------- Resumen ----------
if df_lab is not None and df_exh is not None:
    st.subheader("Resumen de **Archivo laboratorio**")
    st.write(f"Filas: {df_lab.shape[0]}, Columnas: {df_lab.shape[1]}")
    st.dataframe(df_lab.head())

    st.subheader("Resumen de **Exhumaciones**")
    st.write(f"Filas: {df_exh.shape[0]}, Columnas: {df_exh.shape[1]}")
    st.dataframe(df_exh.head())

    # ─────────────────────────────────────────────────────────────
    # CRUCE EXACTO POR CRITERIOS
    # ─────────────────────────────────────────────────────────────
    st.markdown("## Cruce exacto por **Criterio 1 / Criterio 2**")
    colA, colB = st.columns(2)

    # Selección de columnas (las opciones siguen siendo las columnas reales del CSV)
    with colA:
        col_crit1_lab = st.selectbox(
            "Criterio 1 de **Archivo laboratorio**",
            options=df_lab.columns.tolist(),
            index=(df_lab.columns.tolist().index("caso") if "caso" in df_lab.columns else 0)
        )
        col_crit2_lab = st.selectbox(
            "Criterio 2 de **Archivo laboratorio**",
            options=df_lab.columns.tolist(),
            index=(df_lab.columns.tolist().index("Radicado") if "Radicado" in df_lab.columns else 0)
        )

    with colB:
        col_crit1_exh = st.selectbox(
            "Criterio 1 de **Exhumaciones**",
            options=df_exh.columns.tolist(),
            index=(df_exh.columns.tolist().index("caso laboratorio") if "caso laboratorio" in df_exh.columns else 0)
        )
        col_crit2_exh = st.selectbox(
            "Criterio 2 de **Exhumaciones**",
            options=df_exh.columns.tolist(),
            index=(df_exh.columns.tolist().index("Radicado") if "Radicado" in df_exh.columns else 0)
        )

    if st.button("Ejecutar cruce exacto"):
        # Claves normalizadas
        lab = df_lab.copy()
        exh = df_exh.copy()

        lab["_key_crit1"] = lab[col_crit1_lab].map(norm_caso)       # antes _key_caso
        lab["_key_crit2"] = lab[col_crit2_lab].map(norm_radicado)   # antes _key_radicado

        exh["_key_crit1"] = exh[col_crit1_exh].map(norm_caso)
        exh["_key_crit2"] = exh[col_crit2_exh].map(norm_radicado)

        # Coincidencias (inner join)
        coincidencias = lab.merge(
            exh,
            on=["_key_crit1", "_key_crit2"],
            how="inner",
            suffixes=("_lab", "_exh")
        )

        # No coincidentes de Archivo laboratorio (left-anti)
        anti = lab.merge(
            exh[["_key_crit1", "_key_crit2"]],
            on=["_key_crit1", "_key_crit2"],
            how="left",
            indicator=True
        )
        no_coincidentes_lab = lab.loc[anti["_merge"] == "left_only"].drop(columns=["_key_crit1", "_key_crit2"], errors="ignore")

        st.success(f"Coincidencias exactas: {len(coincidencias)} | No coincidentes (Archivo laboratorio): {len(no_coincidentes_lab)}")

        tab1, tab2 = st.tabs(["Coincidencias", "No coincidentes (Archivo laboratorio)"])
        with tab1:
            st.dataframe(coincidencias)
        with tab2:
            st.dataframe(no_coincidentes_lab)

        # ----- Conciliación manual de no coincidentes (Archivo laboratorio) -----
        st.markdown("### Conciliación: agregar manualmente no coincidentes de **Archivo laboratorio** al resultado")

        def etiqueta_fila(row):
            c = str(row.get(col_crit1_lab, ""))
            r = str(row.get(col_crit2_lab, ""))
            return f"[Criterio 2: {r}] Criterio 1: {c}"

        opciones = [etiqueta_fila(row) for _, row in no_coincidentes_lab.iterrows()]
        seleccion = st.multiselect("Selecciona filas para agregarlas al resultado", opciones)

        if st.button("Aplicar conciliación y preparar resultado final"):
            # Tomamos las filas seleccionadas de Archivo laboratorio
            sel_idx = [opciones.index(s) for s in seleccion] if seleccion else []
            agregar_lab = no_coincidentes_lab.iloc[sel_idx].copy() if sel_idx else no_coincidentes_lab.iloc[0:0].copy()

            # Renombramos columnas con sufijo _lab para concatenar con 'coincidencias'
            ren = {c: f"{c}_lab" for c in agregar_lab.columns}
            agregar_lab_suf = agregar_lab.rename(columns=ren)

            # Asegurar columnas clave con prefijo
            agregar_lab_suf["_key_crit1"] = agregar_lab[col_crit1_lab].map(norm_caso)
            agregar_lab_suf["_key_crit2"] = agregar_lab[col_crit2_lab].map(norm_radicado)

            # Reindexar columnas para encajar con 'coincidencias'
            cols_final = list(coincidencias.columns)
            for c in agregar_lab_suf.columns:
                if c not in cols_final:
                    cols_final.append(c)

            # --- Coincidencias aproximadas (difusas) ---
            if 'aproximados' in locals() and len(aproximados) > 0:
                df_aproximados = pd.DataFrame(aproximados).reindex(columns=cols_final)
            else:
                df_aproximados = pd.DataFrame(columns=cols_final)

            # Unión de todos los resultados
            coincidencias_final = pd.concat(
                [coincidencias.reindex(columns=cols_final), agregar_lab_suf.reindex(columns=cols_final), df_aproximados],
                ignore_index=True
            )

            st.success(f"Resultado final listo: {len(coincidencias_final)} filas (exactas, manuales y aproximadas)")
            st.dataframe(coincidencias_final)

            # Descargas
            # CSV
            csv_final = coincidencias_final.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar resultado final (CSV)",
                data=csv_final,
                file_name="coincidencias_final.csv",
                mime="text/csv"
            )

            # XLSX (incluye hojas útiles)
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                coincidencias.to_excel(writer, index=False, sheet_name="coincidencias_exactas")
                agregar_lab_suf.to_excel(writer, index=False, sheet_name="agregados_lab")
                df_aproximados.to_excel(writer, index=False, sheet_name="coincidencias_aproximadas")
                coincidencias_final.to_excel(writer, index=False, sheet_name="resultado_final")
                for sheet in ["coincidencias_exactas", "agregados_lab", "coincidencias_aproximadas", "resultado_final"]:
                    ws = writer.sheets[sheet]
                    ws.set_zoom(90)
            buf.seek(0)
            st.download_button(
                "Descargar resultado final (XLSX)",
                data=buf.getvalue(),
                file_name="coincidencias_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────
    # Coincidencia aproximada (difusa)
    # ─────────────────────────────────────────────────────────────
    st.markdown("## Coincidencia aproximada (difusa)")

    columnas_lab = st.multiselect(
        "Columnas de **Archivo laboratorio** para comparar:",
        options=df_lab.columns.tolist(),
        default=['NOMBRE OCCISO'] if 'NOMBRE OCCISO' in df_lab.columns else []
    )
    columnas_exh = st.multiselect(
        "Columnas de **Exhumaciones** para comparar:",
        options=df_exh.columns.tolist(),
        default=['NOMBRE OCCISO'] if 'NOMBRE OCCISO' in df_exh.columns else []
    )

    if columnas_lab and columnas_exh:
        sensibilidad = st.slider(
            "Grado de sensibilidad (0.0–1.0):",
            min_value=0.0, max_value=1.0, value=0.8, step=0.01
        )
        total_comparaciones = len(df_lab) * len(df_exh)
        tiempo_estimado = total_comparaciones / 10000
        st.info(f"Se realizarán aprox. {total_comparaciones:,} comparaciones. Tiempo estimado: {tiempo_estimado:.1f} s.")

        aproximados = []
        usados_exh = set()
        progress_bar = st.progress(0, text="Comparando registros...")

        for idx_lab, row_lab in df_lab.iterrows():
            valor_lab = " ".join([str(row_lab[col]) for col in columnas_lab])

            valores_exh_disponibles = df_exh.loc[~df_exh.index.isin(usados_exh), columnas_exh].astype(str).agg(" ".join, axis=1)
            valores_exh_disponibles = valores_exh_disponibles.tolist()

            mejores = difflib.get_close_matches(
                valor_lab,
                valores_exh_disponibles,
                n=1,
                cutoff=sensibilidad
            )
            if mejores:
                valor_exh = mejores[0]
                mask_disponibles = ~df_exh.index.isin(usados_exh)
                indices_disponibles = df_exh.index[mask_disponibles]
                idx_exh = None
                for i, v in zip(indices_disponibles, valores_exh_disponibles):
                    if v == valor_exh:
                        idx_exh = i
                        break
                if idx_exh is not None:
                    usados_exh.add(idx_exh)
                    similitud = difflib.SequenceMatcher(None, valor_lab, valor_exh).ratio()
                    # aquí continuarías con tu lógica para armar 'aproximados'
