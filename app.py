import pandas as pd
import streamlit as st 

url = 'https://github.com/juliandariogiraldoocampo/ia_taltech/raw/refs/heads/main/fiscalia/datos_generales_ficticios.csv'
df = pd.read_csv(url, sep=';', encoding='utf-8')

st.dataframe(df)

#selected_columns = ['FECHA_HECHOS', 'DELITO', 'ETAPA', 'FISCAL_ASIGNADO', 'DEPARTAMENTO', 'MUNICIPIO']
#df = df[selected_columns].sort_values(by='FECHA_HECHOS' )

#CONSTRUIR LA PÁGINA
#st.set_page_config(page_title="Dashboard de Delitos - Fiscalía" layout=centered) 
#st.header("Dashboard de Delitos - Fiscalía")
#st.dataframe(df)

st.subheader("Tipo de Delito")
delitos = df['DELITO'].value_counts()
st.bar_chart(delitos)