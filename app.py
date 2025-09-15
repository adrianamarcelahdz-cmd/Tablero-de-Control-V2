import pandas as pd
import streamlit as st 
import plotly.express as px 

url = 'https://github.com/juliandariogiraldoocampo/ia_taltech/raw/refs/heads/main/fiscalia/datos_generales_ficticios.csv'
df = pd.read_csv(url, sep=';', encoding='utf-8')

#st.dataframe(df)

#Crea lista de las columnas que me interasan en su propio orden:
selected_columns = ['FECHA_HECHOS', 'DELITO', 'ETAPA', 'FISCAL_ASIGNADO', 'DEPARTAMENTO', 'MUNICIPIO_HECHOS']
#Actualizar el dtaframe -df- con las columnas de interes ordendas por fecha y reseteo de indice: 
df = df[selected_columns].sort_values(by='FECHA_HECHOS', ascending=True). reset_index(drop=True)

#Convertir fecha object a fecha 
df['FECHA_HECHOS'] = pd.to_datetime(df['FECHA_HECHOS'], errors='coerce')

df_serie_tiempo = df.copy()
#Extraigo solo la fecha sin hora
df['FECHA_HECHOS'] = df['FECHA_HECHOS'].dt.date


#Cálculo de los municipio con mas delitos 
#.upper() para poner en mayuscula 
max_municipio = df ['MUNICIPIO_HECHOS'].value_counts().index[0].upper()


max_cantidad_municipio = df ['MUNICIPIO_HECHOS'].value_counts().iloc[0]
#st.write(f'## Cantidad de Eventos: {max_cantidad_municipio}')

#________________________________________Construcción de página
#https://color.adobe.com/es/
st.set_page_config(page_title= "Dashboard de Delitos - Fiscalía", layout="wide")
st.markdown(
    """
    <style>
        .block-container {
            padding: 3rem 2rem 2rem 3rem;
            max-width: 1600px; 
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.image('img/encabezado.png', use_container_width=True)

#st.header("Dashboard de Delitos - Fiscalía")
st.dataframe(df)

st.write(f"## Municipio con más delitos: {max_municipio} con {max_cantidad_municipio} reportes")

#st.subheader("Tipo de Delito")
#delitos = df['DELITO'].value_counts()
#st.bar_chart(delitos)

#Cálculo etapa mas recurrente 
#.upper() para poner en mayuscula 
etapa_max_frecuente = df ['ETAPA'].value_counts().index[0].upper()
cant_etapa_max_frecuente = df ['ETAPA'].value_counts().iloc[0]
st.write(f"## Etapa más frecuente: {etapa_max_frecuente} con {cant_etapa_max_frecuente} registros")

#Graficar: 
st.subheader('Comportamiento Delitos')
delitos = df['DELITO'].value_counts()
#st.write(delitos)
st.bar_chart(delitos)

#Departamentos con más casos 
max_casos_dep = df ['DEPARTAMENTO'].value_counts().index[0].upper()
cant_max_casos_dep = df ['DEPARTAMENTO'].value_counts().iloc[0]
st.write(f"Departamento con más registros: {max_casos_dep} con {cant_max_casos_dep} registros")

st.subheader('Departamento con más registros')
departamento = df['DEPARTAMENTO'].value_counts()
#st.write(departamento)
st.subheader('Grafica departamento')
st.bar_chart(departamento)

st.subheader('Dsitribución por departamentos')
fig = px.pie(
    values=departamento.values, 
    names=departamento.index,
)
fig.update_traces(textposition='outside', textinfo='percent+label')
fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig)

#Grafico de barras apiladas 
df_delitos = df.groupby(['DEPARTAMENTO', 'DELITO']).size().reset_index(name='conteo')
fig = px.bar(df_delitos, x='DEPARTAMENTO', y='conteo', color='DELITO', barmode='stack')
st.plotly_chart(fig)
st.write(df_delitos)

#Crar columnas xra tarjetas 
col1, col2, col3, col4 = st.columns(4)

#TARJETAS 
#Tarjeta 1 municipio con mas delitos
with col1:
    st.markdown(f"""<h3 style='color:#F2A88D; 
                background-color:#FFF6F5; 
                border: 2px solid #F2A88D; 
                border-radius: 10px; padding: 
                10px; text-align: center'> Muncipio con más delitos :<br> {max_municipio.upper()}</h3><br>""",
                unsafe_allow_html=True
)

#Tarjeta 2 Cantidad delitos
with col2:
    st.markdown(f"""<h3 style='color:#254A59; 
                background-color:#05F2F2; 
                border: 2px solid #05F2F2; 
                border-radius: 10px; padding: 
                10px; text-align: center'> Delitos reportados: <br> {max_cantidad_municipio} </h3><br>""",
                unsafe_allow_html=True
    )

#Trajeta 3 
