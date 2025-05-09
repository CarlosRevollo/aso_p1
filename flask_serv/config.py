"""
Archivo de configuración centralizada para la aplicación APP_LOGS
Mantiene todas las configuraciones en un solo lugar para facilitar cambios
"""
import os
from datetime import datetime, timedelta

# Configuración de la aplicación Flask
class Config:
    """
    Clase de configuración principal para la aplicación Flask.
    
    Contiene ajustes globales como el modo de depuración, el host,
    el puerto y la clave secreta.
    
    Attributes:
        DEBUG (bool): Flag para activar/desactivar el modo de depuración
        HOST (str): Dirección IP donde se ejecutará el servidor
        PORT (int): Puerto en el que escuchará el servidor
        SECRET_KEY (str): Clave secreta para firmar sesiones y otros datos
    """
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    SECRET_KEY = 'clave_secreta_para_la_aplicacion'  # Deberías cambiar esto en producción

# Configuración de la base de datos MariaDB
class DatabaseConfig:
    """
    Configuración de conexión a la base de datos MariaDB.
    
    Define los parámetros de conexión a la base de datos y proporciona
    un método para obtener la configuración en un formato adecuado para
    mysql-connector.
    
    Attributes:
        HOST (str): Nombre o dirección IP del servidor de base de datos
        USER (str): Nombre de usuario para la conexión
        PASSWORD (str): Contraseña para la conexión
        DATABASE (str): Nombre de la base de datos
    """
    HOST = 'localhost'
    USER = 'gabriel'
    PASSWORD = 'gabo123'
    DATABASE = 'bdlogs'
    
    @classmethod
    def get_db_config(cls):
        """
        Retorna la configuración de la base de datos como diccionario.
        
        Este método facilita la obtención de los parámetros de conexión en un
        formato adecuado para usar con mysql-connector.
        
        Returns:
            dict: Diccionario con las credenciales y parámetros de conexión
        """
        return {
            'host': cls.HOST,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'database': cls.DATABASE
        }

# Funciones de utilidad para fechas
def formatear_fecha(fecha_str, es_fecha_fin=False):
    """
    Formatea una cadena de fecha para consultas SQL.
    
    Convierte una fecha en formato string a un formato compatible con
    consultas SQL. Maneja múltiples formatos de entrada:
    - ISO 8601 (YYYY-MM-DDTHH:mm)
    - Fecha simple (YYYY-MM-DD)
    
    Args:
        fecha_str (str): Fecha en formato 'YYYY-MM-DD' o 'YYYY-MM-DDThh:mm'
        es_fecha_fin (bool): Indica si la fecha es de fin de período
        
    Returns:
        str: Fecha formateada en formato 'YYYY-MM-DD HH:mm:ss' o None si hay error
    """
    if not fecha_str:
        return None
    
    try:
        if "T" in fecha_str:  # Formato ISO con hora incluida
            fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
            if es_fecha_fin:
                # Si es fecha fin y no tiene segundos, poner al final del minuto
                fecha = fecha + timedelta(minutes=1) - timedelta(seconds=1)
            return fecha.strftime("%Y-%m-%d %H:%M:%S")
        
        # Solo formato de fecha (YYYY-MM-DD)
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        if es_fecha_fin:
            # Si es fecha fin, poner al final del día
            fecha = fecha + timedelta(days=1) - timedelta(seconds=1)
        return fecha.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Error al formatear fecha: {fecha_str} - {str(e)}")
        return None

# Funciones auxiliares para las plantillas
def get_empty_filters():
    """
    Retorna un diccionario de filtros vacío para usar en las plantillas.
    
    Esta función es útil para inicializar el diccionario de filtros
    en las rutas que no necesitan filtrar resultados o para reiniciar
    los filtros.
    
    Returns:
        dict: Diccionario con claves de filtro inicializadas a None
    """
    return {
        'servicio': None,
        'ip': None,
        'fecha_inicio': None,
        'fecha_fin': None,
        'keyword': None
    }