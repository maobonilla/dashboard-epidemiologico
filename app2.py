import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl
import datetime 

# 1. Configuración principal de la página
st.set_page_config(page_title="Informe Eventos VE01", layout="wide", page_icon="📊")
st.title("Informe Eventos VE01 🩺")

# 2. Carga del archivo XLSX
archivo_cargado = st.file_uploader("Cargar archivo Excel de los Eventos VE01 (.xlsx)", type=["xlsx"])

if archivo_cargado is not None:
    # Leer el archivo
    df = pd.read_excel(archivo_cargado)

    # 3. Limpieza y preparación de datos
    # Llenar espacios en blanco en la columna CentroSalud
    if 'CentroSalud' in df.columns:
        df['CentroSalud'] = df['CentroSalud'].fillna('EBAIS BAGACES 3')

    # Agregar columna VALOR con el número 1 en cada fila
    df['VALOR'] = 1
    # Reemplazar todos los valores que empiecen con "DIABETES MELL" por "DIABETES MELLITUS"
    df.loc[df['DescripcionDX'].str.startswith('DIABETES MELL', na=False), 'DescripcionDX'] = 'DIABETES MELLITUS'

    # Asegurar que FechaDiagnostico tenga el formato de fecha correcto
    if 'FechaDiagnostico' in df.columns:
        df['FechaDiagnostico'] = pd.to_datetime(df['FechaDiagnostico']).dt.date

    # 4. Filtro interactivo en la barra lateral
    st.sidebar.header("Opciones de Filtro")
    lista_diagnosticos = df['DescripcionDX'].dropna().unique().tolist()
    lista_diagnosticos.sort()

    # Casilla desplegable para seleccionar el evento
    evento_seleccionado = st.sidebar.selectbox(
        "Seleccione el tipo de evento (Diagnóstico):",
        options=["Todos los eventos"] + lista_diagnosticos
    )

    # Aplicar el filtro al DataFrame
    if evento_seleccionado != "Todos los eventos":
        df_filtrado = df[df['DescripcionDX'] == evento_seleccionado]
    else:
        df_filtrado = df

    if not df_filtrado.empty:
        # --- TARJETAS DE MÉTRICAS (Análisis Adicional Recomendado) ---
        st.markdown("### Resumen Epidemiológico")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Casos", f"{df_filtrado['VALOR'].sum():,}")
        col2.metric("Edad Promedio", f"{df_filtrado['Años'].mean():.1f} años")
        col3.metric("Total Centros Involucrados", df_filtrado['CentroSalud'].nunique())
        col4.metric("Último Caso Registrado", str(df_filtrado['FechaDiagnostico'].max()))

        st.markdown("---")

        # --- CURVA EPIDEMIOLÓGICA POR SEMANA ---

        st.subheader("Curva Epidemiológica (por Semana)")
        
        # Crear columna de semana epidemiológica
        df_filtrado['SemanaEpi'] = df_filtrado['FechaDiagnostico'].dt.isocalendar().week
        df_filtrado['Año'] = df_filtrado['FechaDiagnostico'].dt.year
        
        # Agrupar por año y semana, sumar casos
        curva_df = df_filtrado.groupby(['Año','SemanaEpi'])['VALOR'].sum().reset_index()
        
        # Crear columna combinada para el eje X
        curva_df['Semana'] = curva_df['Año'].astype(str) + "-SE" + curva_df['SemanaEpi'].astype(str)
        
        # Orden cronológico
        curva_df = curva_df.sort_values(['Año','SemanaEpi'], ascending=True)
        
        # Gráfico
        fig_curva = px.bar(
            curva_df, 
            x='Semana', 
            y='VALOR',
            labels={'Semana':'Semana Epidemiológica','VALOR':'Número de Casos'},
            color_discrete_sequence=['#ff4b4b']
        )
        
        st.plotly_chart(fig_curva, use_container_width=True)
        st.markdown("---")
        
        '''# --- CURVA EPIDEMIOLÓGICA ---
        st.subheader("Curva Epidemiológica")
        # Agrupar por fecha y sumar casos
        curva_df = df_filtrado.groupby('FechaDiagnostico')['VALOR'].sum().reset_index()
        # Orden cronológico ascendente
        curva_df = curva_df.sort_values('FechaDiagnostico', ascending=True)

        fig_curva = px.histogram(curva_df, x='FechaDiagnostico', y='VALOR',
                            labels={'FechaDiagnostico': 'Fecha de Diagnóstico', 'VALOR': 'Número de Casos'},
                            color_discrete_sequence=['#ff4b4b'])
        # Llenar el área bajo la curva para un look más profesional
        #fig_curva.update_traces(fill='tozeroy')
        st.plotly_chart(fig_curva, width="stretch")

        st.markdown("---")'''


        # --- DISTRIBUCIÓN POR SEXO Y CENTRO DE SALUD ---
        colA, colB = st.columns(2)

        with colA:
            st.subheader("Distribución por Sexo")
            sexo_df = df_filtrado.groupby('Sexo')['VALOR'].sum().reset_index()
            # Mapear colores estándar
            colores_sexo = {'F': '#FF69B4', 'M': '#4169E1'}
            fig_sexo = px.pie(sexo_df, names='Sexo', values='VALOR', hole=0.4,
                              color='Sexo', color_discrete_map=colores_sexo)
            st.plotly_chart(fig_sexo, use_container_width=True)

        with colB:
            st.subheader("Casos por Centro de Salud")
            centro_df = df_filtrado.groupby('CentroSalud')['VALOR'].sum().reset_index()
            # Ordenar para que el gráfico de barras se vea mejor
            centro_df = centro_df.sort_values('VALOR', ascending=True)
            fig_centro = px.bar(centro_df, x='VALOR', y='CentroSalud', orientation='h',
                                labels={'VALOR': 'Total de Casos', 'CentroSalud': 'Centro de Salud'},
                                color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_centro, use_container_width=True)

        st.markdown("---")

        # --- ANÁLISIS DE EDAD Y DISTRIBUCIÓN ---
        st.subheader("Análisis y Distribución de la Edad")
        colC, colD = st.columns(2)

        with colC:
            # Gráfico de violín/boxplot (Recomendado para ver la distribución y promedios)
            fig_edad_box = px.box(df_filtrado, x='Sexo', y='Años', color='Sexo',
                                  color_discrete_map=colores_sexo,
                                  title="Dispersión y Promedios de Edad según Sexo")
            st.plotly_chart(fig_edad_box, use_container_width=True)

        with colD:
            # Histograma para ver los picos de edades (Recomendado para epidemiología)
            fig_edad_hist = px.histogram(df_filtrado, x='Años', color='Sexo', barmode='overlay',
                                         nbins=20, color_discrete_map=colores_sexo,
                                         title="Histograma de Grupos Etarios",
                                         labels={'Años': 'Edad'})
            st.plotly_chart(fig_edad_hist, use_container_width=True)

        # --- ANÁLISIS ADICIONAL: CASOS POR DÍA DE LA SEMANA ---
        st.markdown("---")
        st.subheader("💡 Análisis Adicional: Patrones de Consulta Semanal")
        st.info("Este gráfico ayuda a identificar los días de mayor afluencia en los centros de salud.")

        # Obtener el día de la semana y traducirlo
        dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        df_filtrado['DiaSemana_Num'] = pd.to_datetime(df_filtrado['FechaDiagnostico']).dt.dayofweek
        df_filtrado['DiaSemana'] = df_filtrado['DiaSemana_Num'].map(dias_map)

        dia_df = df_filtrado.groupby(['DiaSemana_Num', 'DiaSemana'])['VALOR'].sum().reset_index()
        dia_df = dia_df.sort_values('DiaSemana_Num')

        fig_dia = px.bar(dia_df, x='DiaSemana', y='VALOR',
                         labels={'DiaSemana': 'Día de la Semana', 'VALOR': 'Cantidad de Casos'},
                         color_discrete_sequence=['#FFA15A'])
        st.plotly_chart(fig_dia, use_container_width=True)

    else:
        st.warning("No hay datos disponibles para el filtro seleccionado.")
else:
    st.info("Por favor, carga un archivo Excel en el menú superior para comenzar.")
