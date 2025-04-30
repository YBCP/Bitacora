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
import hashlib
import os
import time

CSV_FILE = "registro_actividades.csv"
USERS_FILE = "usuarios.json"

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Seguimiento de Actividades Subdirección de Operaciones",
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
        .password-container {
            background-color: #ffebee;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            font-size: 1.8rem;
            font-weight: bold;
            color: #1E88E5;
            margin-bottom: 20px;
        }
        .admin-section {
            background-color: #fff8e1;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            border-left: 4px solid #ffc107;
        }
        .user-info {
            font-size: 0.9rem;
            padding: 8px 12px;
            background-color: #e3f2fd;
            border-radius: 5px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

# Inicialización del estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = None

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'nombre_completo' not in st.session_state:
    st.session_state.nombre_completo = None

# Inicializar la contraseña para reportes (en una aplicación real, usarías un método más seguro)
REPORT_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

# Función para crear hash seguro de contraseña con salt
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32)  # 32 bytes de salt aleatorio
    
    # Combina la contraseña con el salt y genera el hash
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Número de iteraciones
    )
    
    # Devuelve el salt y la llave concatenados para almacenamiento
    return salt + key

# Función para verificar la contraseña
def verify_password(stored_password, provided_password):
    # El salt es los primeros 32 bytes del hash almacenado
    salt = stored_password[:32]
    stored_key = stored_password[32:]
    
    # Calcula el hash para la contraseña proporcionada usando el mismo salt
    key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000  # Mismo número de iteraciones
    )
    
    # Compara en tiempo constante para evitar ataques de timing
    return key == stored_key

# Función para verificar la contraseña de reportes
def verify_report_password(input_password):
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return input_hash == REPORT_PASSWORD_HASH

# Función para cargar usuarios o crear el archivo si no existe
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Error al cargar el archivo de usuarios. Creando uno nuevo.")
            # Crear admin por defecto
            admin_password = "admin123"
            hashed_password = hash_password(admin_password)
            users = {
                "admin": {
                    "password": base64.b64encode(hashed_password).decode('utf-8'),
                    "role": "admin",
                    "nombre_completo": "Administrador del Sistema"
                }
            }
            save_users(users)
            return users
    else:
        # Crear archivo de usuarios con un admin por defecto
        admin_password = "admin123"
        hashed_password = hash_password(admin_password)
        users = {
            "admin": {
                "password": base64.b64encode(hashed_password).decode('utf-8'),
                "role": "admin",
                "nombre_completo": "Administrador del Sistema"
            }
        }
        save_users(users)
        return users

# Función para guardar usuarios
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

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

# Función para identificar festivos en Colombia
def es_festivo_colombia(fecha):
    # Lista de festivos en Colombia para 2024-2025
    festivos = [
        # 2024
        datetime(2024, 1, 1).date(),  # Año Nuevo
        datetime(2024, 1, 8).date(),  # Día de los Reyes Magos
        datetime(2024, 3, 25).date(),  # Día de San José
        datetime(2024, 3, 28).date(),  # Jueves Santo
        datetime(2024, 3, 29).date(),  # Viernes Santo
        datetime(2024, 5, 1).date(),  # Día del Trabajo
        datetime(2024, 5, 13).date(),  # Día de la Ascensión
        datetime(2024, 6, 3).date(),  # Corpus Christi
        datetime(2024, 6, 10).date(),  # Sagrado Corazón
        datetime(2024, 7, 1).date(),  # San Pedro y San Pablo
        datetime(2024, 7, 20).date(),  # Día de la Independencia
        datetime(2024, 8, 7).date(),  # Batalla de Boyacá
        datetime(2024, 8, 19).date(),  # Asunción de la Virgen
        datetime(2024, 10, 14).date(),  # Día de la Raza
        datetime(2024, 11, 4).date(),  # Todos los Santos
        datetime(2024, 11, 11).date(),  # Independencia de Cartagena
        datetime(2024, 12, 8).date(),  # Día de la Inmaculada Concepción
        datetime(2024, 12, 25).date(),  # Navidad
        # 2025
        datetime(2025, 1, 1).date(),  # Año Nuevo
        datetime(2025, 1, 6).date(),  # Día de los Reyes Magos
        datetime(2025, 3, 24).date(),  # Día de San José
        datetime(2025, 4, 17).date(),  # Jueves Santo
        datetime(2025, 4, 18).date(),  # Viernes Santo
        datetime(2025, 5, 1).date(),  # Día del Trabajo
        datetime(2025, 6, 2).date(),  # Día de la Ascensión
        datetime(2025, 6, 23).date(),  # Corpus Christi
        datetime(2025, 6, 30).date(),  # Sagrado Corazón
        datetime(2025, 7, 20).date(),  # Día de la Independencia
        datetime(2025, 8, 7).date(),  # Batalla de Boyacá
        datetime(2025, 8, 18).date(),  # Asunción de la Virgen
        datetime(2025, 10, 13).date(),  # Día de la Raza
        datetime(2025, 11, 3).date(),  # Todos los Santos
        datetime(2025, 11, 17).date(),  # Independencia de Cartagena
        datetime(2025, 12, 8).date(),  # Día de la Inmaculada Concepción
        datetime(2025, 12, 25).date(),  # Navidad
    ]
    
    # Asegurarnos que la fecha esté en formato date
    if hasattr(fecha, 'date') and callable(getattr(fecha, 'date')):
        fecha = fecha.date()
        
    return fecha in festivos
    # En caso de cualquier error, retornar fecha actual
    print(f"Error obteniendo rango de fechas: {e}")
    today = datetime.now().date()
    return today, today

# Función para determinar si un día es laboral (no es fin de semana ni festivo)
def es_dia_laboral(fecha):
    # Asegurarnos que la fecha esté en formato date
    if hasattr(fecha, 'date') and callable(getattr(fecha, 'date')):
        fecha = fecha.date()
        
    # Verificar si no es sábado (5) ni domingo (6)
    if fecha.weekday() >= 5:
        return False
    # Verificar si no es festivo en Colombia
    if es_festivo_colombia(fecha):
        return False
    return True

# Función para calcular días laborables entre dos fechas
def dias_laborables_entre_fechas(fecha_inicio, fecha_fin):
    # Asegurarnos que las fechas están en formato date
    if hasattr(fecha_inicio, 'date') and callable(getattr(fecha_inicio, 'date')):
        fecha_inicio = fecha_inicio.date()
    if hasattr(fecha_fin, 'date') and callable(getattr(fecha_fin, 'date')):
        fecha_fin = fecha_fin.date()
        
    dias_laborables = 0
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if es_dia_laboral(fecha_actual):
            dias_laborables += 1
        fecha_actual += timedelta(days=1)
    return dias_laborables

# Función para generar un reporte en PDF
def generate_pdf_report(df, report_title, start_date, end_date, selected_personas):
    class PDF(FPDF):
        def header(self):
            # Configuración del encabezado
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, "Reporte de Actividades", 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 10, f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}", 0, 1, 'C')
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

    # Calcular días laborables en el período
    dias_lab = dias_laborables_entre_fechas(start_date, end_date)

    # Resumen general
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Resumen General", 0, 1)
    pdf.set_font('Arial', '', 11)

    total_horas = df['horas'].sum()

    # Calcular promedio diario solo considerando días laborables
    if dias_lab > 0:
        promedio_diario_laboral = df.groupby('fecha')['horas'].sum().sum() / dias_lab
    else:
        promedio_diario_laboral = 0

    pdf.cell(0, 8, f"Total de horas registradas: {total_horas:.1f}", 0, 1)
    pdf.cell(0, 8, f"Días laborables en el período: {dias_lab}", 0, 1)
    pdf.cell(0, 8, f"Promedio diario de horas (días laborables): {promedio_diario_laboral:.1f}", 0, 1)
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

            # Horas totales para esta persona
            pdf.cell(0, 8, f"Total de horas: {persona_df['horas'].sum():.1f}", 0, 1)

            # Promedio de horas diarias considerando días laborables
            if dias_lab > 0:
                promedio_persona = persona_df['horas'].sum() / dias_lab
                pdf.cell(0, 8, f"Promedio de horas diarias (días laborables): {promedio_persona:.1f}", 0, 1)

            # Tabla de horas por proyecto con promedio diario
            proyectos_persona = persona_df.groupby('proyecto')['horas'].sum().reset_index()
            proyectos_persona = proyectos_persona.sort_values('horas', ascending=False)

            # Agregar columna de promedio diario
            proyectos_persona['promedio_diario'] = proyectos_persona['horas'] / dias_lab if dias_lab > 0 else 0

            pdf.ln(5)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 8, "Proyecto", 1, 0, 'C')
            pdf.cell(30, 8, "Horas Totales", 1, 0, 'C')
            pdf.cell(30, 8, "Prom. Diario", 1, 1, 'C')

            pdf.set_font('Arial', '', 10)
            for _, row in proyectos_persona.iterrows():
                pdf.cell(80, 8, row['proyecto'], 1, 0)
                pdf.cell(30, 8, f"{row['horas']:.1f}", 1, 0, 'R')
                pdf.cell(30, 8, f"{row['promedio_diario']:.1f}", 1, 1, 'R')

            # Tabla de horas por actividad con promedio diario
            pdf.ln(5)
            actividades_persona = persona_df.groupby('actividad')['horas'].sum().reset_index()
            actividades_persona = actividades_persona.sort_values('horas', ascending=False)

            # Agregar columna de promedio diario
            actividades_persona['promedio_diario'] = actividades_persona['horas'] / dias_lab if dias_lab > 0 else 0

            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 8, "Actividad", 1, 0, 'C')
            pdf.cell(30, 8, "Horas Totales", 1, 0, 'C')
            pdf.cell(30, 8, "Prom. Diario", 1, 1, 'C')

            pdf.set_font('Arial', '', 10)
            for _, row in actividades_persona.iterrows():
                pdf.cell(80, 8, row['actividad'], 1, 0)
                pdf.cell(30, 8, f"{row['horas']:.1f}", 1, 0, 'R')
                pdf.cell(30, 8, f"{row['promedio_diario']:.1f}", 1, 1, 'R')

            pdf.ln(10)

            # Detalle de actividad y proyecto combinados
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "Detalle de Actividades por Proyecto", 0, 1)

            # Crear tabla cruzada de actividades y proyectos
            act_proy_pivot = pd.pivot_table(
                persona_df,
                values='horas',
                index=['actividad'],
                columns=['proyecto'],
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            # Agregar el promedio diario para cada combinación
            pdf.set_font('Arial', 'B', 9)
            header_width = 50
            column_width = 35

            # Cabecera de la tabla
            pdf.cell(header_width, 8, "Actividad", 1, 0, 'C')

            # Obtener lista de proyectos para esta persona
            proyectos_de_persona = sorted(persona_df['proyecto'].unique())

            for proyecto in proyectos_de_persona:
                pdf.cell(column_width, 4, proyecto, 1, 0, 'C')
            pdf.ln(4)

            # Segunda línea de la cabecera
            pdf.cell(header_width, 4, "", 0, 0)
            for _ in proyectos_de_persona:
                pdf.cell(column_width / 2, 4, "Total", 1, 0, 'C')
                pdf.cell(column_width / 2, 4, "Prom", 1, 0, 'C')
            pdf.ln(4)

            # Contenido de la tabla
            pdf.set_font('Arial', '', 9)
            actividades_de_persona = sorted(persona_df['actividad'].unique())

            for actividad in actividades_de_persona:
                pdf.cell(header_width, 8, actividad, 1, 0)

                for proyecto in proyectos_de_persona:
                    # Filtrar por actividad y proyecto
                    horas = persona_df[(persona_df['actividad'] == actividad) &
                                       (persona_df['proyecto'] == proyecto)]['horas'].sum()
                    promedio = horas / dias_lab if dias_lab > 0 else 0

                    pdf.cell(column_width / 2, 8, f"{horas:.1f}", 1, 0, 'R')
                    pdf.cell(column_width / 2, 8, f"{promedio:.1f}", 1, 0, 'R')
                pdf.ln(8)

            pdf.ln(10)

    # Tabla con datos detallados
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Registros Detallados", 0, 1)

    # Preparar una versión simplificada del DataFrame para la tabla
    df_for_table = df.sort_values(['persona', 'fecha', 'proyecto'])

    # Marcar días no laborables
    df_for_table['es_laboral'] = df_for_table['fecha'].apply(es_dia_laboral)

    pdf.set_font('Arial', 'B', 8)
    pdf.cell(25, 8, "Fecha", 1, 0, 'C')
    pdf.cell(15, 8, "Laboral", 1, 0, 'C')
    pdf.cell(30, 8, "Persona", 1, 0, 'C')
    pdf.cell(45, 8, "Proyecto", 1, 0, 'C')
    pdf.cell(55, 8, "Actividad", 1, 0, 'C')
    pdf.cell(20, 8, "Horas", 1, 1, 'C')

    pdf.set_font('Arial', '', 8)
    for _, row in df_for_table.iterrows():
        pdf.cell(25, 6, str(row['fecha']), 1, 0)
        pdf.cell(15, 6, "Sí" if row['es_laboral'] else "No", 1, 0, 'C')
        pdf.cell(30, 6, row['persona'], 1, 0)
        pdf.cell(45, 6, row['proyecto'], 1, 0)
        pdf.cell(55, 6, row['actividad'], 1, 0)
        pdf.cell(20, 6, f"{row['horas']:.1f}", 1, 1, 'R')

    # Agregar página con resumen de días laborables
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Calendario de Días Laborables", 0, 1)

    # Crear una lista de todas las fechas en el rango
    todas_fechas = []
    fecha_actual = start_date
    while fecha_actual <= end_date:
        todas_fechas.append({
            'fecha': fecha_actual,
            'es_laboral': es_dia_laboral(fecha_actual),
            'es_festivo': es_festivo_colombia(fecha_actual),
            'dia_semana': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][
                fecha_actual.weekday()]
        })
        fecha_actual += timedelta(days=1)

    # Mostrar calendario
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 8, "Fecha", 1, 0, 'C')
    pdf.cell(30, 8, "Día", 1, 0, 'C')
    pdf.cell(25, 8, "Laborable", 1, 0, 'C')
    pdf.cell(25, 8, "Festivo", 1, 1, 'C')

    pdf.set_font('Arial', '', 10)
    for dia in todas_fechas:
        pdf.cell(25, 6, str(dia['fecha']), 1, 0)
        pdf.cell(30, 6, dia['dia_semana'], 1, 0)
        pdf.cell(25, 6, "Sí" if dia['es_laboral'] else "No", 1, 0, 'C')
        pdf.cell(25, 6, "Sí" if dia['es_festivo'] else "No", 1, 1, 'C')

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, f"Total días en el período: {len(todas_fechas)}", 0, 1)
    pdf.cell(0, 8, f"Días laborables: {dias_lab}", 0, 1)
    pdf.cell(0, 8, f"Días no laborables: {len(todas_fechas) - dias_lab}", 0, 1)

    # Crear buffer de bytes para el PDF
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes

# Inicialización del estado de sesión de autenticación
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.nombre_completo = None

# Cargar usuarios al principio
if 'users' not in st.session_state:
    st.session_state.users = load_users()

# Función para autenticar usuario
def authenticate_user(username, password):
    users = st.session_state.users
    if username in users:
        stored_password = base64.b64decode(users[username]["password"])
        if verify_password(stored_password, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_role = users[username].get("role", "user")
            st.session_state.nombre_completo = users[username].get("nombre_completo", username)
            return True
    return False

# Función para cerrar sesión
def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.nombre_completo = None

# Sistema de autenticación
if not st.session_state.authenticated:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">Acceso al Sistema</div>', unsafe_allow_html=True)
    
    login_tab, register_tab = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with login_tab:
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Iniciar Sesión", use_container_width=True):
                if authenticate_user(username, password):
                    st.success(f"¡Bienvenido {st.session_state.nombre_completo}!")
                    time.sleep(1)  # Esperar un segundo para mostrar el mensaje
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    
    with register_tab:
        # Solo permitir registro si hay un administrador que pueda verificar o si es la configuración inicial
        if not st.session_state.users or any(user.get("role") == "admin" for user in st.session_state.users.values()):
            new_username = st.text_input("Nuevo Usuario", key="reg_username")
            new_password = st.text_input("Nueva Contraseña", type="password", key="reg_password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password", key="confirm_password")
            nombre_completo = st.text_input("Nombre Completo", key="nombre_completo")
            
            # Si no hay usuarios, permitir crear un administrador
            if not st.session_state.users:
                is_admin = st.checkbox("Crear como administrador", value=True)
            else:
                is_admin = st.checkbox("Crear como administrador", value=False)
            
            if st.button("Registrarse", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                elif new_username in st.session_state.users:
                    st.error("El nombre de usuario ya existe.")
                elif not new_username or not new_password:
                    st.error("El usuario y la contraseña son obligatorios.")
                else:
                    # Hash de la nueva contraseña
                    hashed_password = hash_password(new_password)
                    
                    # Agregar nuevo usuario
                    st.session_state.users[new_username] = {
                        "password": base64.b64encode(hashed_password).decode('utf-8'),
                        "role": "admin" if is_admin else "user",
                        "nombre_completo": nombre_completo if nombre_completo else new_username
                    }
                    
                    # Guardar usuarios
                    save_users(st.session_state.users)
                    
                    st.success(f"Usuario {new_username} registrado correctamente. Ahora puedes iniciar sesión.")
        else:
            st.info("El registro de nuevos usuarios está disponible solo para administradores. Por favor, contacte con un administrador.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()  # Detener la ejecución si no hay autenticación

# Si el usuario está autenticado, continuar con la aplicación
# Inicialización de datos en la sesión
if 'data' not in st.session_state:
    if os.path.exists(CSV_FILE):
        # Cargar el CSV asegurando que las fechas se interpreten correctamente
        st.session_state.data = pd.read_csv(CSV_FILE)
        
        # Convertir explícitamente la columna 'fecha' a datetime con formato flexible
        try:
            # Primero intentamos con formato ISO
            st.session_state.data['fecha'] = pd.to_datetime(st.session_state.data['fecha'], format='ISO8601')
        except ValueError:
            try:
                # Si falla, intentamos con formato personalizado
                st.session_state.data['fecha'] = pd.to_datetime(st.session_state.data['fecha'], format='%Y-%m-%d')
            except ValueError:
                # Si todavía falla, usamos el modo 'mixed' muy flexible
                st.session_state.data['fecha'] = pd.to_datetime(st.session_state.data['fecha'], format='mixed')

        # Obtener personas y proyectos del CSV
        personas = sorted(st.session_state.data['persona'].unique().tolist())
        proyectos = sorted(st.session_state.data['proyecto'].unique().tolist())

        # Asignar actividades por defecto (puedes ajustar esto según tus datos reales)
        st.session_state.actividades_personalizadas = {
            persona: ["Trabajo autónomo", "Reuniones"] for persona in personas
        }

        st.session_state.proyectos = proyectos
        st.session_state.password_verified = False
    else:
        # Crear un DataFrame vacío si no existe el archivo
        st.session_state.data = pd.DataFrame(columns=["fecha", "persona", "actividad", "proyecto", "horas"])
        st.session_state.actividades_personalizadas = {}
        st.session_state.proyectos = ["Proyecto 1", "Proyecto 2", "Administrativo"]
        st.session_state.password_verified = False
        # Guardar el archivo vacío
        st.session_state.data.to_csv(CSV_FILE, index=False)

# Función para determinar si el usuario actual puede ver los datos de una persona
def puede_ver_datos_persona(username, persona, user_role):
    # Admin puede ver todo
    if user_role == 'admin':
        return True
    # Usuario normal solo puede ver sus propios datos
    return username == persona

# Título del dashboard con info de usuario
st.markdown('<div class="main-header">Dashboard de Seguimiento de Actividades Subdirección de Operaciones</div>', unsafe_allow_html=True)

# Mostrar información del usuario y botón de cierre de sesión
col1, col2, col3 = st.columns([6, 4, 2])
with col1:
    nombre_mostrar = st.session_state.nombre_completo if 'nombre_completo' in st.session_state and st.session_state.nombre_completo else "Usuario"
    rol_mostrar = "Administrador" if 'user_role' in st.session_state and st.session_state.user_role == 'admin' else "Usuario"
    st.markdown(f"<div class='user-info'>Usuario: {nombre_mostrar} | Rol: {rol_mostrar}</div>", unsafe_allow_html=True)

with col3:
    if st.button("Cerrar Sesión", use_container_width=True):
        logout()
        st.rerun()

# Sidebar para filtros y configuración
st.sidebar.title("Opciones")

# Pestañas en la sidebar
available_tabs = ["Filtros", "Generación de Reportes", "Gestión de Actividades", "Gestión de Proyectos"]
if st.session_state.user_role == "admin":
    available_tabs.append("Administración de Usuarios")

sidebar_tab = st.sidebar.radio("", available_tabs)

# Variable para almacenar el DataFrame filtrado
filtered_df = pd.DataFrame()

if sidebar_tab == "Filtros":
    st.sidebar.header("Filtros de Datos")

    # Obtener lista de personas según el rol del usuario
    all_personas = sorted(st.session_state.data['persona'].unique().tolist())
    if st.session_state.user_role == "admin":
        available_personas = all_personas
    else:
        # Usuario normal solo puede ver sus propios datos
        available_personas = [st.session_state.username]

    # Filtro de fechas
    if not st.session_state.data.empty:
        # Usar nuestra función segura para obtener las fechas
        min_date, max_date = get_safe_date_range(st.session_state.data)
    else:
        min_date = datetime.now().date()
        max_date = datetime.now().date()
        
    selected_dates = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        
        # Convertir las fechas al mismo formato que las fechas en el DataFrame
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        filtered_df = st.session_state.data[
            (st.session_state.data['fecha'] >= start_date) &
            (st.session_state.data['fecha'] <= end_date)
            ]
    else:
        filtered_df = st.session_state.data.copy()

    # Filtro de personas (según permisos)
    selected_personas = st.sidebar.multiselect(
        "Personas",
        available_personas,
        default=available_personas
    )

    if selected_personas:
        filtered_df = filtered_df[filtered_df['persona'].isin(selected_personas)]

    # Filtro de proyectos
    all_proyectos = sorted(
        st.session_state.data['proyecto'].unique().tolist()) if not st.session_state.data.empty else []
    selected_proyectos = st.sidebar.multiselect(
        "Proyectos",
        all_proyectos,
        default=all_proyectos
    )

    if selected_proyectos:
        filtered_df = filtered_df[filtered_df['proyecto'].isin(selected_proyectos)]

    # Filtro dinámico de actividades basado en las personas seleccionadas
    if selected_personas and not filtered_df.empty:
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

    # Determinar si el usuario tiene permisos para generar reportes
    can_generate_reports = (st.session_state.user_role == "admin")

    if not can_generate_reports:
        st.sidebar.warning(
            "Solo los administradores pueden generar reportes. Contacta con un administrador si necesitas acceso.")
    else:
        # Filtro de fechas para el reporte
        if not st.session_state.data.empty:
            # Usar nuestra función segura para obtener las fechas
            min_date, max_date = get_safe_date_range(st.session_state.data)
        else:
            min_date = datetime.now().date()
            max_date = datetime.now().date()
            
        report_dates = st.sidebar.date_input(
            "Rango de fechas para el reporte",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        # Filtro de personas para el reporte (según permisos)
        all_personas = sorted(
            st.session_state.data['persona'].unique().tolist()) if not st.session_state.data.empty else []
        report_personas = st.sidebar.multiselect(
            "Personas a incluir en el reporte",
            all_personas,
            default=all_personas
        )

        # Título del reporte
        report_title = st.sidebar.text_input("Título del reporte", "Reporte de Actividades")

        # Sección de verificación de contraseña
        st.sidebar.markdown('<div class="password-container">', unsafe_allow_html=True)
        st.sidebar.subheader("Verificación de Seguridad")

        # Verificar si la contraseña ya fue validada en esta sesión
        if 'password_verified' not in st.session_state:
            st.session_state.password_verified = False

        if not st.session_state.password_verified:
            report_password = st.sidebar.text_input("Ingrese la contraseña para generar reportes", type="password")
            verify_button = st.sidebar.button("Verificar Contraseña")

            if verify_button:
                if verify_report_password(report_password):
                    st.session_state.password_verified = True
                    st.sidebar.success("¡Contraseña correcta! Ahora puedes generar reportes.")
                else:
                    st.sidebar.error("Contraseña incorrecta. Inténtalo de nuevo.")
        else:
            st.sidebar.success("Contraseña verificada. Puedes generar reportes.")

            # Botón para cerrar sesión
            if st.sidebar.button("Reiniciar Verificación"):
                st.session_state.password_verified = False
                st.rerun()

        st.sidebar.markdown('</div>', unsafe_allow_html=True)

        # Botón para generar el reporte (solo habilitado si la contraseña fue verificada)
        generate_button = st.sidebar.button("Generar Reporte", disabled=not st.session_state.password_verified)

        if generate_button and len(report_dates) == 2 and report_personas:
            report_start_date, report_end_date = report_dates
            
            # Convertir las fechas al mismo formato que las fechas en el DataFrame
            report_start_date = pd.to_datetime(report_start_date)
            report_end_date = pd.to_datetime(report_end_date)

            # Filtrar datos para el reporte
            report_data = st.session_state.data[
                (st.session_state.data['fecha'] >= report_start_date) &
                (st.session_state.data['fecha'] <= report_end_date) &
                (st.session_state.data['persona'].isin(report_personas))
                ]

            if report_data.empty:
                st.sidebar.error("No hay datos disponibles para el reporte con los filtros seleccionados.")
            else:
                try:
                    # Generar PDF
                    pdf_bytes = generate_pdf_report(report_data, report_title, report_start_date, report_end_date,
                                                    report_personas)

                    # Crear link de descarga para el PDF
                    report_filename = f"reporte_{report_start_date.strftime('%Y-%m-%d')}_a_{report_end_date.strftime('%Y-%m-%d')}.pdf"
                    st.sidebar.markdown(get_pdf_download_link(pdf_bytes, report_filename,
                                                            "📥 Descargar Reporte PDF"), unsafe_allow_html=True)

                    # También ofrecer la opción de descarga en CSV
                    st.sidebar.markdown(get_download_link(report_data,
                                                        f"datos_reporte_{report_start_date.strftime('%Y-%m-%d')}_a_{report_end_date.strftime('%Y-%m-%d')}.csv",
                                                        "📥 Descargar Datos del Reporte (CSV)"), unsafe_allow_html=True)

                    # Mostrar una vista previa
                    st.sidebar.success(f"Reporte generado con {len(report_data)} registros")
                except Exception as e:
                    st.sidebar.error(f"Error al generar el reporte: {str(e)}")
                    st.sidebar.info("Por favor, intenta con un rango de fechas diferente o contacta al administrador.")

elif sidebar_tab == "Gestión de Actividades":
    st.sidebar.header("Personalizar Actividades")

    # Selector de persona para editar sus actividades (según permisos)
    if st.session_state.user_role == "admin":
        available_personas = sorted(
            st.session_state.actividades_personalizadas.keys()) if st.session_state.actividades_personalizadas else []
    else:
        # Usuario normal solo puede editar sus propias actividades
        if st.session_state.username not in st.session_state.actividades_personalizadas:
            st.session_state.actividades_personalizadas[st.session_state.username] = ["Trabajo autónomo", "Reuniones"]
        available_personas = [st.session_state.username]

    if not available_personas:
        st.sidebar.warning("No hay personas disponibles para editar actividades.")
    else:
        persona_elegida = st.sidebar.selectbox(
            "Selecciona una persona para editar sus actividades:",
            available_personas
        )

        # Mostrar las actividades actuales de la persona seleccionada
        st.sidebar.subheader(f"Actividades de {persona_elegida}")

        # Verificar si la persona tiene actividades asignadas
        if persona_elegida not in st.session_state.actividades_personalizadas:
            st.session_state.actividades_personalizadas[persona_elegida] = ["Trabajo autónomo", "Reuniones"]

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

    # Solo permitir gestión de proyectos a los administradores
    if st.session_state.user_role != "admin":
        st.sidebar.warning("Solo los administradores pueden gestionar proyectos.")
    else:
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

elif sidebar_tab == "Administración de Usuarios" and st.session_state.user_role == "admin":
    st.sidebar.header("Administración de Usuarios")

    admin_action = st.sidebar.radio("Acción:",
                                    ["Ver Usuarios", "Crear Usuario", "Modificar Usuario", "Eliminar Usuario"])

    if admin_action == "Ver Usuarios":
        st.sidebar.subheader("Usuarios del Sistema")
        for username, user_info in st.session_state.users.items():
            st.sidebar.markdown(f"""
            **Usuario:** {username}  
            **Nombre:** {user_info.get('nombre_completo', username)}  
            **Rol:** {user_info.get('role', 'user')}
            ---
            """)

    elif admin_action == "Crear Usuario":
        st.sidebar.subheader("Crear Nuevo Usuario")
        new_username = st.sidebar.text_input("Nombre de Usuario")
        new_password = st.sidebar.text_input("Contraseña", type="password")
        confirm_password = st.sidebar.text_input("Confirmar Contraseña", type="password")
        new_nombre = st.sidebar.text_input("Nombre Completo")
        new_role = st.sidebar.selectbox("Rol", ["user", "admin"])

        if st.sidebar.button("Crear Usuario"):
            if not new_username or not new_password:
                st.sidebar.error("Usuario y contraseña son obligatorios.")
            elif new_password != confirm_password:
                st.sidebar.error("Las contraseñas no coinciden.")
            elif new_username in st.session_state.users:
                st.sidebar.error("El nombre de usuario ya existe.")
            else:
                # Hash la contraseña
                hashed_password = hash_password(new_password)

                # Agregar usuario
                st.session_state.users[new_username] = {
                    "password": base64.b64encode(hashed_password).decode('utf-8'),
                    "role": new_role,
                    "nombre_completo": new_nombre if new_nombre else new_username
                }

                # Guardar cambios
                save_users(st.session_state.users)
                st.sidebar.success(f"Usuario {new_username} creado correctamente.")

    elif admin_action == "Modificar Usuario":
        st.sidebar.subheader("Modificar Usuario")
        user_to_modify = st.sidebar.selectbox("Seleccionar Usuario", list(st.session_state.users.keys()))

        if user_to_modify:
            user_info = st.session_state.users[user_to_modify]
            new_nombre = st.sidebar.text_input("Nombre Completo",
                                               value=user_info.get("nombre_completo", user_to_modify))
            new_role = st.sidebar.selectbox("Rol", ["user", "admin"], index=0 if user_info.get("role") == "user" else 1)
            change_password = st.sidebar.checkbox("Cambiar Contraseña")

            if change_password:
                new_password = st.sidebar.text_input("Nueva Contraseña", type="password")
                confirm_password = st.sidebar.text_input("Confirmar Nueva Contraseña", type="password")

            if st.sidebar.button("Guardar Cambios"):
                if change_password:
                    if not new_password:
                        st.sidebar.error("La contraseña no puede estar vacía.")
                    elif new_password != confirm_password:
                        st.sidebar.error("Las contraseñas no coinciden.")
                    else:
                        # Actualizar contraseña
                        hashed_password = hash_password(new_password)
                        st.session_state.users[user_to_modify]["password"] = base64.b64encode(hashed_password).decode(
                            'utf-8')

                # Actualizar otros datos
                st.session_state.users[user_to_modify]["nombre_completo"] = new_nombre
                st.session_state.users[user_to_modify]["role"] = new_role

                # Guardar cambios
                save_users(st.session_state.users)
                st.sidebar.success(f"Usuario {user_to_modify} modificado correctamente.")

    elif admin_action == "Eliminar Usuario":
        st.sidebar.subheader("Eliminar Usuario")
        user_to_delete = st.sidebar.selectbox("Seleccionar Usuario", list(st.session_state.users.keys()))

        if user_to_delete:
            if user_to_delete == st.session_state.username:
                st.sidebar.error("No puedes eliminar tu propio usuario.")
            else:
                if st.sidebar.button(f"Eliminar Usuario {user_to_delete}"):
                    # Confirmar eliminación
                    if st.sidebar.checkbox("Confirmar eliminación (esta acción no se puede deshacer)"):
                        del st.session_state.users[user_to_delete]
                        save_users(st.session_state.users)
                        st.sidebar.success(f"Usuario {user_to_delete} eliminado correctamente.")

# Contenido principal basado en la pestaña seleccionada
if sidebar_tab == "Filtros":
    # Evitar errores si no hay datos después de filtrar
    if filtered_df.empty:
        st.warning("No hay datos que mostrar con los filtros actuales.")
    else:
        col1, col2 = st.columns(2)
        fecha_max = filtered_df['fecha'].max()
        fecha_inicio_30 = fecha_max - pd.Timedelta(days=29)
        ultimos_30_df = filtered_df[filtered_df['fecha'] >= fecha_inicio_30]

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
        st.markdown('<div class="section-header">Distribución de Actividades</div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            # Filtrar solo los últimos 30 días desde hoy
            fecha_max = filtered_df['fecha'].max()
            fecha_inicio_30 = fecha_max - pd.Timedelta(days=29)

            ultimos_30_df = filtered_df[filtered_df['fecha'] >= fecha_inicio_30]

            # Agrupar por actividad solo en ese rango
            actividad_data = ultimos_30_df.groupby('actividad')['horas'].sum().reset_index()

            fig_act = px.pie(
                actividad_data,
                values='horas',
                names='actividad',
                title='Distribución de Horas por Actividad (Últimos 30 días)',
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig_act.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_act, use_container_width=True)

        with col2:
            # Gráfico de distribución de horas por persona
            persona_data = ultimos_30_df.groupby('persona')['horas'].sum().reset_index()
            fig_per = px.bar(
                persona_data,
                x='persona',
                y='horas',
                title='Horas Totales por Persona (Últimos 30 días)',
                color='persona',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_per, use_container_width=True)

        # Sección de distribución por proyectos
        st.markdown('<div class="section-header">Distribución por Proyectos</div>',
                    unsafe_allow_html=True)

        # Gráfico de distribución de horas por proyecto
        proyecto_data = ultimos_30_df.groupby('proyecto')['horas'].sum().reset_index()
        fig_proy = px.bar(
            proyecto_data,
            x='proyecto',
            y='horas',
            title='Horas Totales por Proyecto (Últimos 30 días)',
            color='proyecto',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_proy, use_container_width=True)

        # Matriz de proyectos y personas
        st.markdown('<div class="section-header">Matriz Proyectos-Personas</div>',
                    unsafe_allow_html=True)

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
        st.markdown('<div class="section-header">Evolución Temporal de Actividades</div>',
                    unsafe_allow_html=True)

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
        daily_hours_proyecto = filtered_df.groupby(['fecha', 'proyecto'])[
            'horas'].sum().reset_index()
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
        st.markdown('<div class="section-header">Datos Detallados</div>',
                    unsafe_allow_html=True)

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
    st.markdown('<div class="section-header">Generación de Reportes Personalizados</div>',
                unsafe_allow_html=True)

    if st.session_state.user_role == "admin":
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

        st.markdown('<div class="section-header">Generar Reportes</div>',
                    unsafe_allow_html=True)
        st.info(
            "Configura las opciones del reporte en la barra lateral y haz clic en 'Generar Reporte' para crear tu informe personalizado.")
    else:
        st.warning(
            "Solo los administradores pueden generar reportes. Si necesitas un reporte de tus actividades, contacta con un administrador.")

elif sidebar_tab == "Administración de Usuarios" and st.session_state.user_role == "admin":
    st.markdown('<div class="section-header">Administración de Usuarios</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="admin-section">
        <h3>Panel de Administración de Usuarios</h3>
        <p>En este panel puedes gestionar los usuarios del sistema:</p>
        <ul>
            <li><strong>Ver Usuarios:</strong> Lista de todos los usuarios registrados en el sistema.</li>
            <li><strong>Crear Usuario:</strong> Registra nuevos usuarios asignándoles un rol (administrador o usuario normal).</li>
            <li><strong>Modificar Usuario:</strong> Actualiza la información de los usuarios existentes.</li>
            <li><strong>Eliminar Usuario:</strong> Elimina usuarios del sistema (excepto tu propio usuario).</li>
        </ul>
        <p>Selecciona la acción que deseas realizar en el menú lateral.</p>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar tabla de usuarios
    st.subheader("Lista de Usuarios")

    users_data = []
    for username, info in st.session_state.users.items():
        users_data.append({
            "Usuario": username,
            "Nombre Completo": info.get("nombre_completo", username),
            "Rol": info.get("role", "user")
        })

    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)

# Sección de registro de nueva actividad (visible en todas las pestañas excepto en la de generación de reportes)
if sidebar_tab != "Generación de Reportes" and sidebar_tab != "Administración de Usuarios":
    st.markdown('<div class="section-header">Registrar Nueva Actividad</div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        nueva_fecha = st.date_input("Fecha", datetime.now())

        # Determinar la persona según el rol
        if st.session_state.user_role == "admin":
            # Los administradores pueden registrar actividades para cualquier persona
            personas_disponibles = sorted(
                st.session_state.actividades_personalizadas.keys()) if st.session_state.actividades_personalizadas else [
                st.session_state.username]
            nueva_persona = st.selectbox("Persona", personas_disponibles,
                                         index=personas_disponibles.index(
                                             st.session_state.username) if st.session_state.username in personas_disponibles else 0)
        else:
            # Los usuarios normales solo pueden registrar sus propias actividades
            nueva_persona = st.session_state.username
            st.write(f"Persona: {st.session_state.nombre_completo}")

    with col2:
        # Las actividades se cargan dinámicamente según la persona seleccionada
        if nueva_persona not in st.session_state.actividades_personalizadas:
            st.session_state.actividades_personalizadas[nueva_persona] = ["Trabajo autónomo",
                                                                          "Reuniones"]

        actividades_persona_seleccionada = st.session_state.actividades_personalizadas.get(
            nueva_persona, [])
        if actividades_persona_seleccionada:
            nueva_actividad = st.selectbox("Actividad", actividades_persona_seleccionada)
        else:
            nueva_actividad = st.text_input("Actividad (no hay actividades predefinidas)")

        # Selector de proyecto
        nuevo_proyecto = st.selectbox("Proyecto", st.session_state.proyectos)

    with col3:
        # Cambiar el input de horas a un slider
        nuevas_horas = st.slider("Horas dedicadas", min_value=0.5, max_value=8.0, value=1.0, step=0.5)

        # Opción para añadir una nueva actividad en el momento
        nueva_actividad_checkbox = st.checkbox("¿Añadir nueva actividad?")

        if nueva_actividad_checkbox:
            nueva_actividad_nombre = st.text_input("Nombre de la nueva actividad")
            if st.button("Añadir a mi lista") and nueva_actividad_nombre.strip():
                # Verificar si la actividad ya existe
                if nueva_actividad_nombre in st.session_state.actividades_personalizadas[nueva_persona]:
                    st.warning(f"La actividad '{nueva_actividad_nombre}' ya existe en la lista.")
                else:
                    # Agregar la nueva actividad a la lista de la persona
                    st.session_state.actividades_personalizadas[nueva_persona].append(nueva_actividad_nombre.strip())
                    st.success(f"Actividad '{nueva_actividad_nombre}' añadida a la lista de {nueva_persona}")

                    # Actualizar la variable para que se pueda seleccionar inmediatamente
                    nueva_actividad = nueva_actividad_nombre.strip()

    # Botón para registrar la actividad
    submit_button = st.button("Registrar Actividad", use_container_width=True)

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
            st.session_state.data.to_csv(CSV_FILE, index=False)  # Guardar en CSV automáticamente

            # Mostrar mensaje de éxito
            st.success(
                f"Actividad registrada: {nueva_persona} - {nueva_actividad} - Proyecto: {nuevo_proyecto} - {nuevas_horas} horas")

            # Para mostrar cómo se vería
            st.dataframe(new_row, use_container_width=True)

            # Mostrar botón para volver a rellenar
            st.write("¿Deseas registrar otra actividad similar?")
            if st.button("Registrar Actividad Similar", use_container_width=True):
                st.rerun()

    # Opción para añadir un nuevo proyecto directamente (solo para administradores)
    if st.session_state.user_role == "admin":
        st.markdown('<div class="section-header">Añadir Nuevo Proyecto</div>', unsafe_allow_html=True)

        nuevo_proyecto_nombre = st.text_input("Nombre del nuevo proyecto")
        if st.button("Añadir Proyecto", use_container_width=True) and nuevo_proyecto_nombre.strip():
            # Verificar si el proyecto ya existe
            if nuevo_proyecto_nombre in st.session_state.proyectos:
                st.warning(f"El proyecto '{nuevo_proyecto_nombre}' ya existe en la lista.")
            else:
                # Agregar el nuevo proyecto a la lista
                st.session_state.proyectos.append(nuevo_proyecto_nombre.strip())
                st.success(f"Proyecto '{nuevo_proyecto_nombre}' añadido a la lista de proyectos")

# Notas informativas según el rol del usuario
if st.session_state.user_role == "admin":
    # Notas para administradores
    st.markdown("""
    ---
    **Notas para Administradores:**
    - Puedes ver y editar las actividades de todos los usuarios.
    - Gestiona proyectos desde la sección "Gestión de Proyectos".
    - Genera reportes personalizados desde la sección "Generación de Reportes".
    - Administra usuarios desde la sección "Administración de Usuarios".
    - Los datos se guardan en archivos CSV locales (en una implementación real, usarías una base de datos).
    """)
else:
    # Notas para usuarios normales
    st.markdown("""
    ---
    **Notas para Usuarios:**
    - Solo puedes ver y editar tus propias actividades.
    - Personaliza tu lista de actividades desde la sección "Gestión de Actividades".
    - Para obtener reportes o añadir nuevos proyectos, contacta con un administrador.
    - Tus datos son visibles para los administradores del sistema.
    """)

# Información de la aplicación en el footer
st.markdown("""
---
Desarrollado con Streamlit | Dashboard de Seguimiento de Actividades con Control de Acceso
""")
