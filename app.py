import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
import json
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Seguimiento de Actividades",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 20px;
        }
        .section-header {
            font-size: 1.8rem;
            font-weight: bold;
            color: #0D47A1;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .metric-container {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .report-section {
            background-color: #e8f4f8;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
        }
    </style>
    """, unsafe_allow_html=True)

# Inicialización de datos en la sesión
if 'data' not in st.session_state:
    # Generar fechas para los últimos 30 días
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    dates = [start_date + timedelta(days=i) for i in range(30)]

    # Lista de personas
    personas = ["Cesar Ramirez","Cristian Martínez","Nestor Roldan","Hernan Bernal","Daniel Morales","Leila Awad","Ninfa Carolina Menjura","Yair Morales","Daniel Gonzalez","Diana Carvajal","Diego Marin","Jairo Perdomo","Laura Rodríguez","Luz Carolina Galvis","Maria Bernate","Martha Vargas"]

    # Proyectos de ejemplo
    proyectos = ["Datos Temáticos", "Cartografía", "Análisis de Datos", "Mapa de Referencia"]

    # Actividades personalizadas por persona
    actividades_personalizadas = {
    "Cesar Ramirez": ["Trabajo autónomo", "Reuniones"],
    "Cristian Martínez": ["Trabajo autónomo", "Reuniones"],
    "Nestor Roldan": ["Trabajo autónomo", "Reuniones"],
    "Hernan Bernal": ["Trabajo autónomo", "Reuniones"],
    "Daniel Morales": ["Trabajo autónomo", "Reuniones"],
    "Leila Awad": ["Trabajo autónomo", "Reuniones"],
    "Ninfa Carolina Menjura": ["Trabajo autónomo", "Reuniones"],
    "Yair Morales": ["Trabajo autónomo", "Reuniones"],
    "Daniel Gonzalez": ["Trabajo autónomo", "Reuniones"],
    "Diana Carvajal": ["Trabajo autónomo", "Reuniones"],
    "Diego Marin": ["Trabajo autónomo", "Reuniones"],
    "Jairo Perdomo": ["Trabajo autónomo", "Reuniones"],
    "Laura Rodríguez": ["Trabajo autónomo", "Reuniones"],
    "Luz Carolina Galvis": ["Trabajo autónomo", "Reuniones"],
    "Maria Bernate": ["Trabajo autónomo", "Reuniones"],
    "Martha Vargas": ["Trabajo autónomo", "Reuniones"],
    }

    # Guardar las actividades personalizadas en la sesión
    st.session_state.actividades_personalizadas = actividades_personalizadas

    # Generar datos iniciales
    data = []
    for fecha in dates:
        for persona in personas:
            # Para cada persona y fecha, generar datos para diferentes actividades
            actividades_persona = actividades_personalizadas[persona]
            for actividad in actividades_persona:
                # Algunas actividades podrían no tener horas en ciertos días
                if np.random.random() > 0.3:  # 70% de probabilidad de tener la actividad
                    horas = round(np.random.uniform(1, 8), 1)  # Entre 1 y 8 horas, con un decimal
                    proyecto = np.random.choice(proyectos)  # Asignar un proyecto aleatorio
                    data.append({
                        "fecha": fecha,
                        "persona": persona,
                        "actividad": actividad,
                        "proyecto": proyecto,
                        "horas": horas
                    })

    # Guardar los datos en un DataFrame y en la sesión
    st.session_state.data = pd.DataFrame(data)

    # Guardar la lista de proyectos en la sesión
    st.session_state.proyectos = proyectos


# Función para crear un link de descarga
def get_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Función para crear un link de descarga para PDF
def get_pdf_download_link(pdf_bytes, filename, text):
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Función para generar un reporte en PDF
def generate_pdf_report(df, report_title, start_date, end_date, selected_personas):
    class PDF(FPDF):
        def header(self):
            # Configuración del encabezado
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, "Reporte de Actividades", 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 10, f"Periodo: {start_date} a {end_date}", 0, 1, 'C')
            self.ln(5)

        def footer(self):
            # Configuración del pie de página
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    # Crear PDF
    pdf = PDF()
    pdf.add_page()

    # Título del reporte
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, report_title, 0, 1)
    pdf.ln(5)

    # Resumen general
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Resumen General", 0, 1)
    pdf.set_font('Arial', '', 11)

    total_horas = df['horas'].sum()
    promedio_diario = df.groupby('fecha')['horas'].sum().mean()

    pdf.cell(0, 8, f"Total de horas registradas: {total_horas:.1f}", 0, 1)
    pdf.cell(0, 8, f"Promedio diario de horas: {promedio_diario:.1f}", 0, 1)
    pdf.cell(0, 8, f"Personas incluidas: {', '.join(selected_personas)}", 0, 1)
    pdf.ln(5)

    # Detalles por persona
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Detalle por Persona", 0, 1)

    for persona in selected_personas:
        persona_df = df[df['persona'] == persona]
        if not persona_df.empty:  # Solo mostrar si hay datos para esta persona
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"{persona}", 0, 1)
            pdf.set_font('Arial', '', 11)

            # Horas totales por proyecto para esta persona
            pdf.cell(0, 8, f"Total de horas: {persona_df['horas'].sum():.1f}", 0, 1)

            # Tabla de horas por proyecto
            proyectos_persona = persona_df.groupby('proyecto')['horas'].sum().reset_index()
            proyectos_persona = proyectos_persona.sort_values('horas', ascending=False)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(100, 8, "Proyecto", 1, 0, 'C')
            pdf.cell(40, 8, "Horas", 1, 1, 'C')

            pdf.set_font('Arial', '', 10)
            for _, row in proyectos_persona.iterrows():
                pdf.cell(100, 8, row['proyecto'], 1, 0)
                pdf.cell(40, 8, f"{row['horas']:.1f}", 1, 1, 'R')

            # Tabla de horas por actividad
            pdf.ln(5)
            actividades_persona = persona_df.groupby('actividad')['horas'].sum().reset_index()
            actividades_persona = actividades_persona.sort_values('horas', ascending=False)

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(100, 8, "Actividad", 1, 0, 'C')
            pdf.cell(40, 8, "Horas", 1, 1, 'C')

            pdf.set_font('Arial', '', 10)
            for _, row in actividades_persona.iterrows():
                pdf.cell(100, 8, row['actividad'], 1, 0)
                pdf.cell(40, 8, f"{row['horas']:.1f}", 1, 1, 'R')

            pdf.ln(10)

    # Tabla con datos detallados
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Registros Detallados", 0, 1)

    # Preparar una versión simplificada del DataFrame para la tabla
    df_for_table = df.sort_values(['persona', 'fecha', 'proyecto'])

    pdf.set_font('Arial', 'B', 8)
    pdf.cell(25, 8, "Fecha", 1, 0, 'C')
    pdf.cell(30, 8, "Persona", 1, 0, 'C')
    pdf.cell(55, 8, "Proyecto", 1, 0, 'C')
    pdf.cell(60, 8, "Actividad", 1, 0, 'C')
    pdf.cell(20, 8, "Horas", 1, 1, 'C')

    pdf.set_font('Arial', '', 8)
    for _, row in df_for_table.iterrows():
        pdf.cell(25, 6, str(row['fecha']), 1, 0)
        pdf.cell(30, 6, row['persona'], 1, 0)
        pdf.cell(55, 6, row['proyecto'], 1, 0)
        pdf.cell(60, 6, row['actividad'], 1, 0)
        pdf.cell(20, 6, f"{row['horas']:.1f}", 1, 1, 'R')

    # Crear buffer de bytes para el PDF
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_bytes = pdf_output.getvalue()
    pdf_output.close()
    return pdf_bytes


# Título del dashboard
st.markdown('<div class="main-header">Dashboard de Seguimiento de Actividades</div>', unsafe_allow_html=True)

# Sidebar para filtros y configuración
st.sidebar.title("Opciones")

# Pestañas en la sidebar
sidebar_tab = st.sidebar.radio("",
                               ["Filtros", "Generación de Reportes", "Gestión de Actividades", "Gestión de Proyectos"])

if sidebar_tab == "Filtros":
    st.sidebar.header("Filtros de Datos")

    # Filtro de fechas
    min_date = st.session_state.data['fecha'].min()
    max_date = st.session_state.data['fecha'].max()
    selected_dates = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = st.session_state.data[(st.session_state.data['fecha'] >= start_date) &
                                            (st.session_state.data['fecha'] <= end_date)]
    else:
        filtered_df = st.session_state.data.copy()

    # Filtro de personas
    all_personas = sorted(st.session_state.data['persona'].unique().tolist())
    selected_personas = st.sidebar.multiselect(
        "Personas",
        all_personas,
        default=all_personas
    )

    if selected_personas:
        filtered_df = filtered_df[filtered_df['persona'].isin(selected_personas)]

    # Filtro de proyectos
    all_proyectos = sorted(st.session_state.data['proyecto'].unique().tolist())
    selected_proyectos = st.sidebar.multiselect(
        "Proyectos",
        all_proyectos,
        default=all_proyectos
    )

    if selected_proyectos:
        filtered_df = filtered_df[filtered_df['proyecto'].isin(selected_proyectos)]

    # Filtro dinámico de actividades basado en las personas seleccionadas
    if selected_personas:
        # Recopilar todas las actividades de las personas seleccionadas
        actividades_disponibles = filtered_df['actividad'].unique().tolist()
        selected_actividades = st.sidebar.multiselect(
            "Actividades",
            sorted(actividades_disponibles),
            default=actividades_disponibles
        )

        if selected_actividades:
            filtered_df = filtered_df[filtered_df['actividad'].isin(selected_actividades)]

    # Link para descargar datos filtrados
    st.sidebar.markdown(get_download_link(filtered_df, "datos_actividades.csv",
                                          "📥 Descargar datos filtrados"), unsafe_allow_html=True)

elif sidebar_tab == "Generación de Reportes":
    st.sidebar.header("Configuración del Reporte")

    # Filtro de fechas para el reporte
    min_date = st.session_state.data['fecha'].min()
    max_date = st.session_state.data['fecha'].max()
    report_dates = st.sidebar.date_input(
        "Rango de fechas para el reporte",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filtro de personas para el reporte
    all_personas = sorted(st.session_state.data['persona'].unique().tolist())
    report_personas = st.sidebar.multiselect(
        "Personas a incluir en el reporte",
        all_personas,
        default=all_personas
    )

    # Título del reporte
    report_title = st.sidebar.text_input("Título del reporte", "Reporte de Actividades")

    # Botón para generar el reporte
    if st.sidebar.button("Generar Reporte") and len(report_dates) == 2 and report_personas:
        report_start_date, report_end_date = report_dates

        # Filtrar datos para el reporte
        report_data = st.session_state.data[
            (st.session_state.data['fecha'] >= report_start_date) &
            (st.session_state.data['fecha'] <= report_end_date) &
            (st.session_state.data['persona'].isin(report_personas))
            ]

        if report_data.empty:
            st.sidebar.error("No hay datos disponibles para el reporte con los filtros seleccionados.")
        else:
            # Generar PDF
            pdf_bytes = generate_pdf_report(report_data, report_title, report_start_date, report_end_date,
                                            report_personas)

            # Crear link de descarga para el PDF
            report_filename = f"reporte_{report_start_date}_a_{report_end_date}.pdf"
            st.sidebar.markdown(get_pdf_download_link(pdf_bytes, report_filename,
                                                      "📥 Descargar Reporte PDF"), unsafe_allow_html=True)

            # También ofrecer la opción de descarga en CSV
            st.sidebar.markdown(get_download_link(report_data,
                                                  f"datos_reporte_{report_start_date}_a_{report_end_date}.csv",
                                                  "📥 Descargar Datos del Reporte (CSV)"), unsafe_allow_html=True)

            # Mostrar una vista previa
            st.sidebar.success(f"Reporte generado con {len(report_data)} registros")

elif sidebar_tab == "Gestión de Actividades":
    st.sidebar.header("Personalizar Actividades")

    # Selector de persona para editar sus actividades
    persona_elegida = st.sidebar.selectbox(
        "Selecciona una persona para editar sus actividades:",
        sorted(st.session_state.actividades_personalizadas.keys())
    )

    # Mostrar las actividades actuales de la persona seleccionada
    st.sidebar.subheader(f"Actividades de {persona_elegida}")

    # Convertir la lista de actividades a un string para edición
    actividades_actuales = st.session_state.actividades_personalizadas[persona_elegida]
    actividades_texto = "\n".join(actividades_actuales)

    # Área de texto para editar actividades
    nuevas_actividades_texto = st.sidebar.text_area(
        "Edita las actividades (una por línea):",
        value=actividades_texto,
        height=200
    )

    # Botón para guardar cambios
    if st.sidebar.button("Guardar Cambios"):
        # Convertir el texto a una lista de actividades
        nuevas_actividades = [act.strip() for act in nuevas_actividades_texto.split("\n") if act.strip()]

        # Actualizar las actividades en el diccionario
        st.session_state.actividades_personalizadas[persona_elegida] = nuevas_actividades

        # Mostrar mensaje de éxito
        st.sidebar.success(f"Actividades actualizadas para {persona_elegida}")

        # Nota sobre los datos históricos
        st.sidebar.info("Nota: Los cambios no afectan a los datos históricos ya registrados.")

elif sidebar_tab == "Gestión de Proyectos":
    st.sidebar.header("Gestionar Proyectos")

    # Mostrar los proyectos actuales
    st.sidebar.subheader("Proyectos Actuales")

    # Convertir la lista de proyectos a un string para edición
    proyectos_actuales = st.session_state.proyectos
    proyectos_texto = "\n".join(proyectos_actuales)

    # Área de texto para editar proyectos
    nuevos_proyectos_texto = st.sidebar.text_area(
        "Edita los proyectos (uno por línea):",
        value=proyectos_texto,
        height=200
    )

    # Botón para guardar cambios
    if st.sidebar.button("Guardar Cambios"):
        # Convertir el texto a una lista de proyectos
        nuevos_proyectos = [proy.strip() for proy in nuevos_proyectos_texto.split("\n") if proy.strip()]

        # Actualizar la lista de proyectos en la sesión
        st.session_state.proyectos = nuevos_proyectos

        # Mostrar mensaje de éxito
        st.sidebar.success("Lista de proyectos actualizada")

        # Nota sobre los datos históricos
        st.sidebar.info("Nota: Los cambios no afectan a los datos históricos ya registrados.")

# Contenido principal basado en la pestaña seleccionada
if sidebar_tab == "Filtros":
    # Evitar errores si no hay datos después de filtrar
    if filtered_df.empty:
        st.warning("No hay datos que mostrar con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)

        # Métricas principales
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Horas Registradas", f"{filtered_df['horas'].sum():.1f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            promedio_horas_diarias = filtered_df.groupby('fecha')['horas'].sum().mean()
            st.metric("Promedio Horas Diarias", f"{promedio_horas_diarias:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Sección 1: Distribución de Actividades
        st.markdown('<div class="section-header">Distribución de Actividades</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de distribución de horas por actividad
            actividad_data = filtered_df.groupby('actividad')['horas'].sum().reset_index()
            fig_act = px.pie(
                actividad_data,
                values='horas',
                names='actividad',
                title='Distribución de Horas por Actividad',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_act.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_act, use_container_width=True)

        with col2:
            # Gráfico de distribución de horas por persona
            persona_data = filtered_df.groupby('persona')['horas'].sum().reset_index()
            fig_per = px.bar(
                persona_data,
                x='persona',
                y='horas',
                title='Horas Totales por Persona',
                color='persona',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_per, use_container_width=True)

        # Sección de distribución por proyectos
        st.markdown('<div class="section-header">Distribución por Proyectos</div>', unsafe_allow_html=True)

        # Gráfico de distribución de horas por proyecto
        proyecto_data = filtered_df.groupby('proyecto')['horas'].sum().reset_index()
        fig_proy = px.bar(
            proyecto_data,
            x='proyecto',
            y='horas',
            title='Horas Totales por Proyecto',
            color='proyecto',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_proy, use_container_width=True)

        # Matriz de proyectos y personas
        st.markdown('<div class="section-header">Matriz Proyectos-Personas</div>', unsafe_allow_html=True)

        # Crear una tabla cruzada de proyectos por personas
        matriz_proy_pers = pd.pivot_table(
            filtered_df,
            values='horas',
            index='proyecto',
            columns='persona',
            aggfunc='sum',
            fill_value=0
        )

        # Mostrar como heatmap
        fig_matriz = px.imshow(
            matriz_proy_pers,
            text_auto='.1f',
            color_continuous_scale='Blues',
            title='Distribución de Horas por Proyecto y Persona'
        )
        fig_matriz.update_layout(height=400)
        st.plotly_chart(fig_matriz, use_container_width=True)

        # Sección 2: Evolución Temporal
        st.markdown('<div class="section-header">Evolución Temporal de Actividades</div>', unsafe_allow_html=True)

        # Gráfico de línea de horas diarias
        daily_hours = filtered_df.groupby(['fecha', 'persona'])['horas'].sum().reset_index()
        fig_evol = px.line(
            daily_hours,
            x='fecha',
            y='horas',
            color='persona',
            title='Evolución de Horas Registradas por Día',
            markers=True
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # Evolución por proyecto
        daily_hours_proyecto = filtered_df.groupby(['fecha', 'proyecto'])['horas'].sum().reset_index()
        fig_evol_proy = px.line(
            daily_hours_proyecto,
            x='fecha',
            y='horas',
            color='proyecto',
            title='Evolución de Horas por Proyecto',
            markers=True
        )
        st.plotly_chart(fig_evol_proy, use_container_width=True)

        # Sección 4: Tabla de Datos Detallados
        st.markdown('<div class="section-header">Datos Detallados</div>', unsafe_allow_html=True)

        # Añadir un input para filtrar por texto
        search_term = st.text_input("Buscar en los datos:", "")
        if search_term:
            search_results = filtered_df[
                filtered_df['persona'].str.contains(search_term, case=False) |
                filtered_df['actividad'].str.contains(search_term, case=False) |
                filtered_df['proyecto'].str.contains(search_term, case=False)
                ]
            st.dataframe(search_results, use_container_width=True)
        else:
            st.dataframe(filtered_df, use_container_width=True)

elif sidebar_tab == "Generación de Reportes":
    # Contenido principal para la pestaña de generación de reportes
    st.markdown('<div class="section-header">Generación de Reportes Personalizados</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="report-section">
        <h3>Instrucciones para Generar Reportes</h3>
        <p>Para generar un reporte personalizado, sigue estos pasos:</p>
        <ol>
            <li>En la barra lateral, selecciona el rango de fechas para el reporte.</li>
            <li>Elige las personas que deseas incluir en el reporte.</li>
            <li>Establece un título para tu reporte.</li>
            <li>Haz clic en el botón "Generar Reporte".</li>
            <li>Una vez generado, podrás descargar el reporte en formato PDF o los datos en CSV.</li>
        </ol>
        <p>Los reportes incluyen:</p>
        <ul>
            <li>Resumen general con total de horas y promedios.</li>
            <li>Detalle por persona con horas por proyecto y actividad.</li>
            <li>Listado completo de registros de actividades.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Vista Previa del Formato de Reporte</div>', unsafe_allow_html=True)

    # Mostrar una imagen o descripción del formato del reporte
    st.image("https://via.placeholder.com/800x400.png?text=Vista+Previa+del+Formato+de+Reporte",
             caption="Ejemplo de formato de reporte PDF", use_container_width=True)

    st.info(
        "Configura las opciones del reporte en la barra lateral y haz clic en 'Generar Reporte' para crear tu informe personalizado.")

# Sección de registro de nueva actividad (visible en todas las pestañas excepto en la de generación de reportes)
if sidebar_tab != "Generación de Reportes":
    st.markdown('<div class="section-header">Registrar Nueva Actividad</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        nueva_fecha = st.date_input("Fecha", datetime.now())
        nueva_persona = st.selectbox("Persona", sorted(st.session_state.actividades_personalizadas.keys()))

    with col2:
        # Las actividades se cargan dinámicamente según la persona seleccionada
        actividades_persona_seleccionada = st.session_state.actividades_personalizadas.get(nueva_persona, [])
        if actividades_persona_seleccionada:
            nueva_actividad = st.selectbox("Actividad", actividades_persona_seleccionada)
        else:
            nueva_actividad = st.text_input("Actividad (no hay actividades predefinidas)")

        # Selector de proyecto
        nuevo_proyecto = st.selectbox("Proyecto", st.session_state.proyectos)

    with col3:
        # Cambiar el input de horas a un slider
        nuevas_horas = st.slider("Horas dedicadas", min_value=0.5, max_value=12.0, value=4.0, step=0.5)

        # Opción para añadir una nueva actividad en el momento
        nueva_actividad_checkbox = st.checkbox("¿Añadir nueva actividad?")

        if nueva_actividad_checkbox:
            nueva_actividad_nombre = st.text_input("Nombre de la nueva actividad")
            if st.button("Añadir a mi lista") and nueva_actividad_nombre.strip():
                # Agregar la nueva actividad a la lista de la persona
                st.session_state.actividades_personalizadas[nueva_persona].append(nueva_actividad_nombre.strip())
                st.success(f"Actividad '{nueva_actividad_nombre}' añadida a la lista de {nueva_persona}")

                # Actualizar la variable para que se pueda seleccionar inmediatamente
                nueva_actividad = nueva_actividad_nombre.strip()

    # Botón para registrar la actividad
    submit_button = st.button("Registrar Actividad")

    if submit_button:
        # Validar los datos
        if not nueva_actividad:
            st.error("Por favor, selecciona o ingresa una actividad.")
        else:
            # En una aplicación real, aquí guardaríamos los datos en una base de datos
            # Para este ejemplo, añadimos a nuestro DataFrame en memoria
            new_row = pd.DataFrame([{
                "fecha": nueva_fecha,
                "persona": nueva_persona,
                "actividad": nueva_actividad,
                "proyecto": nuevo_proyecto,
                "horas": nuevas_horas
            }])
            
            # Actualizar DataFrame en session_state
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            
            # Mostrar mensaje de éxito
            st.success(f"Actividad registrada: {nueva_persona} - {nueva_actividad} - Proyecto: {nuevo_proyecto} - {nuevas_horas} horas")
            
            # Para mostrar cómo se vería
            st.dataframe(new_row, use_container_width=True)

    # Opción para añadir un nuevo proyecto directamente
    st.markdown('<div class="section-header">Añadir Nuevo Proyecto</div>', unsafe_allow_html=True)

    nuevo_proyecto_nombre = st.text_input("Nombre del nuevo proyecto")
    if st.button("Añadir Proyecto") and nuevo_proyecto_nombre.strip():
        # Verificar si el proyecto ya existe
        if nuevo_proyecto_nombre in st.session_state.proyectos:
            st.warning(f"El proyecto '{nuevo_proyecto_nombre}' ya existe en la lista.")
        else:
            # Agregar el nuevo proyecto a la lista
            st.session_state.proyectos.append(nuevo_proyecto_nombre.strip())
            st.success(f"Proyecto '{nuevo_proyecto_nombre}' añadido a la lista de proyectos")

# Notas informativas
st.markdown("""
---
**Notas:**
- Este dashboard permite a cada persona mantener su propia lista personalizada de actividades.
- Se pueden añadir nuevas actividades desde la sección de "Gestión de Actividades" en la barra lateral o al registrar una nueva actividad.
- Los proyectos pueden ser administrados desde la sección "Gestión de Proyectos" en la barra lateral o añadiendo un nuevo proyecto directamente.
- Los reportes personalizados se pueden generar desde la sección "Generación de Reportes" en la barra lateral.
- En una implementación real, los datos se guardarían en una base de datos persistente.
""")

# Información de la aplicación en el footer
st.markdown("""
---
Desarrollado con Streamlit | Dashboard de Seguimiento de Actividades y Proyectos
""")
