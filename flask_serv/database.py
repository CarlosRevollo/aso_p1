import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from datetime import datetime, timedelta
from config import DatabaseConfig, formatear_fecha

# Configuración de la base de datos MariaDB desde config.py
db_config = DatabaseConfig.get_db_config()

# Crear un pool de conexiones para mejorar el rendimiento
try:
    pool = MySQLConnectionPool(
        pool_name="app_logs_pool",
        pool_size=5,
        **db_config
    )
    print("Pool de conexiones creado exitosamente")
except Error as err:
    print(f"Error al crear el pool de conexiones: {err}")
    pool = None

def get_connection():
    """
    Obtiene una conexión a la base de datos desde el pool o crea una nueva conexión.
    
    El uso de un pool de conexiones permite la reutilización de conexiones, reduciendo
    la sobrecarga de crear nuevas conexiones para cada consulta. Si el pool no está 
    disponible, se crea una conexión directa como fallback.
    
    Returns:
        MySQLConnection: Objeto de conexión a la base de datos, o None si hay un error.
    """
    try:
        if pool:
            return pool.get_connection()
        else:
            return mysql.connector.connect(**db_config)
    except Error as err:
        print(f"Error al obtener conexión: {err}")
        return None

def construir_condiciones(filtros, campo_ip, campo_fecha, campo_detalle):
    """
    Construye las condiciones SQL y los parámetros de consulta basados en los filtros.
    
    Esta función centraliza la lógica de construcción de condiciones WHERE para
    diferentes tablas, facilitando la reutilización y mantenimiento del código.
    
    Args:
        filtros (dict): Diccionario con los filtros aplicados por el usuario
        campo_ip (str): Nombre del campo que contiene la dirección IP en la tabla
        campo_fecha (str): Nombre del campo que contiene la fecha/hora en la tabla
        campo_detalle (str): Nombre del campo que contiene los detalles/mensaje en la tabla
        
    Returns:
        tuple: Una tupla con (cláusula WHERE, lista de parámetros)
    """
    condiciones = []
    params = []
    
    # Formateo de fechas
    fecha_inicio = formatear_fecha(filtros['fecha_inicio'], False)
    fecha_fin = formatear_fecha(filtros['fecha_fin'], True)
    
    if filtros['ip']:
        condiciones.append(f"{campo_ip} LIKE %s")
        params.append(f"%{filtros['ip']}%")
    if fecha_inicio:
        condiciones.append("fecha_hora >= %s")
        params.append(fecha_inicio)
    if fecha_fin:
        condiciones.append("fecha_hora <= %s")
        params.append(fecha_fin)
    if filtros['keyword']:
        condiciones.append(f"{campo_detalle} LIKE %s")
        params.append(f"%{filtros['keyword']}%")
        
    where_clause = " AND ".join(condiciones)
    if where_clause:
        where_clause = "WHERE " + where_clause
        
    return where_clause, params

def obtener_eventos(filtros, page=1, per_page=50):
    """
    Obtiene eventos de logs de múltiples fuentes (Apache, FTP) aplicando filtros.
    
    Esta función unifica la búsqueda a través de diferentes tablas de logs y devuelve
    un conjunto unificado de resultados. Utiliza subconsultas y UNION para combinar
    resultados de diferentes servicios.
    
    Args:
        filtros (dict): Un diccionario con los siguientes filtros opcionales:
            - servicio (str): Tipo de servicio ('Apache', 'FTP', 'Todos')
            - ip (str): Dirección IP a filtrar
            - fecha_inicio (str): Fecha de inicio en formato 'YYYY-MM-DD' o 'YYYY-MM-DDThh:mm'
            - fecha_fin (str): Fecha de fin en formato 'YYYY-MM-DD' o 'YYYY-MM-DDThh:mm'
            - keyword (str): Palabra clave a buscar en los detalles del log
        page (int): Número de página para paginación (empieza en 1)
        per_page (int): Cantidad de registros por página
            
    Returns:
        tuple: (eventos, total_registros)
            - eventos: Lista de diccionarios, cada uno representando un evento de log
            - total_registros: Total de registros que cumplen con los filtros (sin paginar)
    """
    connection = None
    try:
        connection = get_connection()
        if not connection:
            return [], 0
            
        cursor = connection.cursor(dictionary=True)

        subqueries = []
        params = []

        # Depuración
        print(f"Filtros aplicados: {filtros}")
        
        # Apache - registros_acceso
        if not filtros['servicio'] or filtros['servicio'] in ['Todos', 'Apache']:
            where_acceso, params_acceso = construir_condiciones(
                filtros, 'ip', 'fecha_hora', 'ruta'
            )
            subqueries.append(f"""
                SELECT 'Apache (Acceso)' AS tipo, fecha_hora, ip, ruta AS detalle
                FROM registros_acceso
                {where_acceso}
            """)
            params.extend(params_acceso)

        # Apache - registros_error
        if not filtros['servicio'] or filtros['servicio'] in ['Todos', 'Apache']:
            where_error, params_error = construir_condiciones(
                filtros, 'cliente', 'fecha_hora', 'mensaje'
            )
            subqueries.append(f"""
                SELECT 'Apache (Error)' AS tipo, fecha_hora, cliente AS ip, mensaje AS detalle
                FROM registros_error
                {where_error}
            """)
            params.extend(params_error)

        # FTP - registros_ftp
        if not filtros['servicio'] or filtros['servicio'] in ['Todos', 'FTP']:
            where_ftp, params_ftp = construir_condiciones(
                filtros, 'ip', 'fecha_hora', 'detalles'
            )
            subqueries.append(f"""
                SELECT 'FTP' AS tipo, fecha_hora, ip, detalles AS detalle
                FROM registros_ftp
                {where_ftp}
            """)
            params.extend(params_ftp)

        # Ejecutar consultas si hay alguna
        if not subqueries:
            return [], 0
        else:
            # Primero, obtener el total de registros para la paginación
            union_query = " UNION ALL ".join(subqueries)
            count_query = f"SELECT COUNT(*) as total FROM ({union_query}) AS count_query"
            cursor.execute(count_query, tuple(params))
            total_registros = cursor.fetchone()['total']
            
            # Luego, obtener los resultados paginados
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT * FROM ({union_query}) AS subquery
                ORDER BY fecha_hora DESC
                LIMIT {per_page} OFFSET {offset}
            """
            print(f"SQL Query: {data_query}")
            print(f"Params: {params}")
            
            cursor.execute(data_query, tuple(params))
            eventos = cursor.fetchall()
            print(f"Eventos encontrados: {len(eventos)}")

        cursor.close()
        return eventos, total_registros

    except Error as err:
        print(f"Error al consultar la base de datos: {err}")
        return [], 0
    finally:
        if connection:
            try:
                # Si es una conexión de pool, se devuelve al pool
                # Si es una conexión directa, se cierra
                connection.close()
            except Error:
                pass

def get_all_registros_acceso():
    """
    Obtiene estadísticas de los registros de acceso agrupados por fecha.
    
    Esta función recupera datos estadísticos de la tabla de registros de acceso,
    incluyendo el total de accesos por día, la cantidad de IPs únicas y
    el número de errores (códigos de estado entre 400 y 599).
    
    Returns:
        list: Lista de diccionarios con estadísticas diarias, cada uno con las llaves:
            - fecha (date): La fecha del registro
            - total_accesos (int): Número total de accesos en ese día
            - ips_unicas (int): Número de direcciones IP únicas que accedieron ese día
            - errores (int): Número de respuestas con código de error (400-599)
    """
    connection = None
    try:
        connection = get_connection()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Obtener registros de acceso con estadísticas adicionales
        query = """
            SELECT 
                DATE(fecha_hora) as fecha,
                COUNT(*) as total_accesos,
                COUNT(DISTINCT ip) as ips_unicas,
                SUM(CASE WHEN codigo_estado BETWEEN 400 AND 599 THEN 1 ELSE 0 END) as errores
            FROM registros_acceso
            GROUP BY DATE(fecha_hora)
            ORDER BY fecha DESC
            LIMIT 30
        """
        
        cursor.execute(query)
        registros = cursor.fetchall()
        
        cursor.close()
        return registros

    except Error as err:
        print(f"Error al consultar la base de datos: {err}")
        return []
    finally:
        if connection:
            try:
                connection.close()
            except Error:
                pass