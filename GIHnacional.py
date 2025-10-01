# --- Salvaguardas previas ---
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Recuperar df_combined si no está en variables locales (por ejemplo, tras un rerun)
if 'df_combined' not in locals():
    df_combined = st.session_state.get('df_combined', None)

# Si no hay DataFrame combinado, detén el resto del script de forma segura
if not isinstance(df_combined, pd.DataFrame):
    st.info("Aún no se ha generado el DataFrame combinado. Carga y combina los archivos primero.")
    st.stop()

# --- Mostrar un resumen básico ---
st.write(f"DataFrame combinado: {df_combined.shape[0]} filas y {df_combined.shape[1]} columnas.")
st.dataframe(df_combined.head())

# --- Dashboard ---
st.header("Dashboard")

# Línea de tiempo - Las fechas están en las columnas J, K y L (índices 9, 10, 11)
st.subheader("Línea de tiempo (columnas J, K y L)")
date_cols = []
for idx in [9, 10, 11]:
    if idx < len(df_combined.columns):
        date_cols.append(df_combined.columns[idx])

if date_cols:
    # Convertir a datetime con coerción
    for col in date_cols:
        df_combined[col] = pd.to_datetime(df_combined[col], errors='coerce')

    # Unir todas las fechas en una sola serie para el gráfico
    fechas_list = [df_combined[c].dropna() for c in date_cols if c in df_combined.columns]
    if fechas_list:
        fechas = pd.concat(fechas_list) if len(fechas_list) > 1 else fechas_list[0]
        timeline = fechas.value_counts().sort_index().reset_index()
        timeline.columns = ['Fecha', 'Conteo']

        if not timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(timeline['Fecha'], timeline['Conteo'], marker='o')
            ax.set_title("Línea de Tiempo - Conteo por Fecha (J, K, L)")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Conteo")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No hay datos de fecha válidos en las columnas J, K o L.")
    else:
        st.info("No se pudieron consolidar fechas para la línea de tiempo.")
else:
    st.info("No se encontraron las columnas J, K y L para la línea de tiempo.")

# --- Tarjetas con insights ---
st.subheader("Insights destacados")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Filas totales", df_combined.shape[0])
col2.metric("Columnas totales", df_combined.shape[1])
col3.metric("Datos nulos (%)", round(df_combined.isnull().mean().mean() * 100, 2))
col4.metric("Valores únicos cols.", int((df_combined.nunique() > 1).sum()))

# --- Top 10 value counts ---
st.subheader("Top 10 valores más frecuentes")
categorical_cols = df_combined.select_dtypes(include=["object", "category"]).columns.tolist()
if categorical_cols:
    col = st.selectbox("Selecciona columna para top 10 value counts", categorical_cols)
    if col in df_combined.columns:
        top10 = df_combined[col].value_counts(dropna=False).nlargest(10)
        st.bar_chart(top10)
    else:
        st.info("La columna seleccionada ya no existe en el DataFrame.")
else:
    st.info("No hay columnas categóricas para mostrar value counts.")

# --- Descarga del CSV resultante ---
st.header("Descargar archivo consolidado")
try:
    csv = df_combined.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV combinado",
        data=csv,
        file_name='archivo_consolidado.csv',
        mime='text/csv'
    )
except Exception as e:
    st.error(f"No se pudo generar el CSV para descarga: {e}")
