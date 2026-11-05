import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openpyxl
import datetime as dt 
import io

tab1, tab2, tab3 = st.tabs(["Informe VE01", "Canal Endémico", "Canal Endémico IVRS"])
with tab1:        
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
    
        df_filtrado['FechaDiagnostico'] = pd.to_datetime(df_filtrado['FechaDiagnostico'], errors='coerce')
        
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
    
        # --- Construcción del HTML completo ---
        total_casos = df_filtrado['VALOR'].sum()
        edad_prom = df_filtrado['Años'].mean()
        centros = df_filtrado['CentroSalud'].nunique
        ultimo_caso = str(df_filtrado['FechaDiagnostico'].max())
        
        
        html_parts = []
        
        # Encabezado y métricas
        html_parts.append(f"""
        <h1>Informe Eventos VE01</h1>
        <h2>Resumen Epidemiológico</h2>
       
        
        <ul>
            <li>Total de Casos: {total_casos:,}</li>
            <li>Edad Promedio: {edad_prom:.1f} años</li>
            <li>Total Centros Involucrados: {centros}</li>
            <li>Último Caso Registrado: {ultimo_caso}</li>
        </ul>
        """)
    
        # Gráficos convertidos a HTML
        html_parts.append(fig_curva.to_html(full_html=False, include_plotlyjs='cdn'))
        html_parts.append(fig_sexo.to_html(full_html=False, include_plotlyjs=False))
    
        # Concatenar todo (ahora sí son solo strings)
        full_html = "<html><head><meta charset='utf-8'></head><body>" + "".join(html_parts) + "</body></html>"
    
        # Botón de descarga
        st.download_button(
            label="📥 Descargar Informe Completo en HTML",
            data=full_html,
            file_name="informe_eventos_VE01.html",
            mime="text/html")    
    else:
        st.warning("No hay datos disponibles para el filtro seleccionado.")
else:
    st.info("Por favor, carga un archivo Excel en el menú superior para comenzar.")

with tab2: 
    st.header("Canal Endémico 📈")
    st.info("Aquí se mostrará la información del canal endémico.")

    # Ejemplo: gráfico simulado de canal endémico
    import numpy as np
    semanas = list(range(1, 53))
    casos_observados = np.random.randint(5, 20, size=52)
    canal_min = np.random.randint(3, 10, size=52)
    canal_max = canal_min + np.random.randint(5, 15, size=52)

    canal_df = pd.DataFrame({
        "Semana": semanas,
        "Casos Observados": casos_observados,
        "Canal Min": canal_min,
        "Canal Max": canal_max
    })

    fig_canal = px.line(canal_df, x="Semana", y=["Casos Observados", "Canal Min", "Canal Max"],
                        labels={"value":"Número de Casos","Semana":"Semana Epidemiológica"},
                        title="Canal Endémico")
    st.plotly_chart(fig_canal, use_container_width=True)
    
with tab3: 
    # --- Datos fijos para canal endémico ---
    zona_exito = [130.66,121.37,82.00,47.76,110.85,61.26,34.82,115.59,163.89,142.46,
    122.52,96.34,74.74,96.61,123.79,95.65,131.47,131.65,107.12,150.18,143.41,
    146.76,138.27,197.43,156.94,161.55,200.01,254.39,180.98,127.78,100.66,
    79.94,121.14,145.37,101.26,133.35,150.75,171.56,149.43,161.02,165.67,
    195.43,156.17,154.57,128.10,119.88,142.68,96.93,129.08,125.08,107.14,142.60]
    
    zona_seguridad = [41,23,66,76,55,36,41,21,26,47,45,62,35,49,8,31,18,29,83,6,
    27,47,50,96,138,95,48,40,27,41,35,40,28,21,53,35,18,18,50,34,5,16,22,18,
    40,39,47,43,19,37,41,38]
    
    zona_alerta = [54,27,120,200,83,58,89,25,30,63,62,102,51,74,9,41,21,36,147,7,
    33,62,69,143,259,150,60,47,31,54,48,61,35,25,82,44,21,20,68,42,5,17,26,20,
    52,51,63,63,21,49,56,48]
    
    # --- Pestaña Canal Endémico ---
    st.title("Canal Endémico IVRS - Área de Salud Bagaces 2026")
      
    st.header("Canal Endémico IVRS")
    file_xlsx = st.file_uploader("Cargar archivo VE02 .xlsx", type=["xlsx"])
    # 2. Carga del archivo XLSX
if file_xlsx is not None:
    # Leer el archivo
    df = pd.read_excel(file_xlsx)
    
    # 3. Limpieza y preparación de datos
    # Llenar espacios en blanco en la columna CentroSalud
    
if 'CentroSalud' in df.columns:
    df['CentroSalud'] = df['CentroSalud'].fillna('EBAIS BAGACES 3')

    semanas = list(range(1, len(zona_exito)+1))
    media  = [e+s for e,s in zip(zona_exito, zona_seguridad)]
    ic_sup = [m+a for m,a in zip(media, zona_alerta)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=semanas,y=zona_exito,fill="tozeroy",
                             fillcolor="rgba(0,180,0,0.95)",line=dict(width=0),
                             name="Éxito"))
    fig.add_trace(go.Scatter(x=semanas,y=media,fill="tonexty",
                             fillcolor="rgba(255,200,0,0.95)",line=dict(width=0),
                             name="Seguridad"))
    fig.add_trace(go.Scatter(x=semanas,y=ic_sup,fill="tonexty",
                             fillcolor="rgba(220,0,0,0.95)",line=dict(width=0),
                             name="Alerta"))

    # 1) Filtra Evento = IVRS
    df = df[df["DescripcionEvento"].astype(str).str.contains(r"\bIVRS\b", case=False, na=False)].copy()

    masc = {
        "<1": "COL_Masc_Menos_1_ANO",
        "1-4": "COL_Masc_De_1_4_ANO",
        "5-19": ["COL_Masc_De_5_9_ANO", "COL_Masc_De_10_14_ANO", "COL_Masc_De_15_19_ANO"],
        "20-39": ["COL_Masc_De_20_24_ANO", "COL_Masc_De_25_29_ANO", "COL_Masc_De_30_34_ANO",
                  "COL_Masc_De_35_39_ANO"],
        "40-64": ["COL_Masc_De_40_44_ANO", "COL_Masc_De_45_49_ANO", "COL_Masc_De_50_54_ANO",
                  "COL_Masc_De_55_59_ANO", "COL_Masc_De_60_64_ANO"],
        "65+": "COL_Masc_65_y_mas",
    }

    fem = {
        "<1": "COL_Fem_Menos_1_ANO",
        "1-4": "COL_Fem_De_1_4_ANO",
        "5-19": ["COL_Fem_De_5_9_ANO", "COL_Fem_De_10_14_ANO", "COL_Fem_De_15_19_ANO"],
        "20-39": ["COL_Fem_De_20_24_ANO", "COL_Fem_De_25_29_ANO", "COL_Fem_De_30_34_ANO", "COL_Fem_De_35_39_ANO"],
        "40-64": ["COL_Fem_De_40_44_ANO", "COL_Fem_De_45_49_ANO", "COL_Fem_De_50_54_ANO", "COL_Fem_De_55_59_ANO",
                  "COL_Fem_De_60_64_ANO"],
        "65+": "COL_Fem_65_y_mas",
    }

    # 3) columnas necesarias
    needed_cols = []
    for d in (masc, fem):
        for v in d.values():
            needed_cols += v if isinstance(v, list) else [v]

    needed_cols = [c for c in needed_cols if c in df.columns]

    if needed_cols:
        df[needed_cols] = df[needed_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    def sum_cols(spec):
        if isinstance(spec, list):
            cols = [c for c in spec if c in df.columns]
            return df[cols].sum(axis=1) if cols else 0
        return df[spec] if spec in df.columns else 0

    # 4) grupos (Masc + Fem)
    df["<1"] = sum_cols(masc["<1"]) + sum_cols(fem["<1"])
    df["1-4"] = sum_cols(masc["1-4"]) + sum_cols(fem["1-4"])
    df["5-19"] = sum_cols(masc["5-19"]) + sum_cols(fem["5-19"])
    df["20-39"] = sum_cols(masc["20-39"]) + sum_cols(fem["20-39"])
    df["40-64"] = sum_cols(masc["40-64"]) + sum_cols(fem["40-64"])
    df["65+"] = sum_cols(masc["65+"]) + sum_cols(fem["65+"])

    df["Total"] = df[["<1", "1-4", "5-19", "20-39", "40-64", "65+"]].sum(axis=1)

    if file_xlsx:
        df = pd.read_excel(file_xlsx)
        df = df[df["Evento"].str.contains("IVRS", case=False)]
        tot = df.groupby("SemEpi")["COL_Total"].sum()
        lista = [None]*len(semanas)
        for wk, val in tot.items():
            if 1 <= wk <= len(semanas):
                lista[int(wk)-1] = int(val)
        fig.add_trace(go.Scatter(x=semanas,y=lista,
                                 mode="lines+markers",
                                 line=dict(color="black",width=2),
                                 name="Año en curso"))

    st.plotly_chart(fig, use_container_width=True)



