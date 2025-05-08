"""
Aplicación principal para APP_LOGS - Sistema de visualización y análisis de logs.

Este módulo implementa la aplicación web Flask que permite visualizar, 
filtrar y analizar logs de diferentes servicios como Apache y FTP.
"""
from flask import Flask, render_template, request, send_file, jsonify, make_response, url_for
import csv
import json
from io import StringIO
import os
import tempfile
from math import ceil
from database import obtener_eventos, get_all_registros_acceso
from config import Config, get_empty_filters

# Inicialización de la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Ruta principal que muestra los eventos de logs con filtros.
    
    Esta vista permite a los usuarios ver eventos recientes de logs
    y filtrarlos por diferentes criterios como servicio, IP, fechas y palabras clave.
    Implementa paginación para navegar a través de grandes conjuntos de datos.
    
    Returns:
        str: Renderiza la plantilla index.html con los eventos y filtros aplicados
    """
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Captura los filtros del formulario o de la URL
    if request.method == 'POST':
        filtros = {
            'servicio': request.form.get('servicio'),
            'ip': request.form.get('ip'),
            'fecha_inicio': request.form.get('fecha_inicio'),
            'fecha_fin': request.form.get('fecha_fin'),
            'keyword': request.form.get('keyword')
        }
        # Reiniciar a la primera página al aplicar filtros
        page = 1
    else:
        # Preservar filtros en la URL para paginación
        filtros = {
            'servicio': request.args.get('servicio'),
            'ip': request.args.get('ip'),
            'fecha_inicio': request.args.get('fecha_inicio'),
            'fecha_fin': request.args.get('fecha_fin'),
            'keyword': request.args.get('keyword')
        }

    # Obtener eventos filtrados con paginación
    eventos, total = obtener_eventos(filtros, page, per_page)
    
    # Calcular información de paginación
    total_pages = ceil(total / per_page) if total > 0 else 1
    
    return render_template(
        "index.html", 
        eventos=eventos, 
        filtros=filtros,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    )

@app.route("/exportar", methods=['GET'])
def exportar_datos():
    """
    Ruta para exportar los datos filtrados en formato CSV o JSON.
    
    Esta función permite descargar los eventos filtrados en formato CSV o JSON.
    Utiliza los mismos filtros que la página principal y soporta exportación completa
    (sin límite de registros).
    
    Returns:
        Response: Un archivo CSV o JSON para descarga
    """
    formato = request.args.get('formato', 'csv')
    
    # Obtener los mismos filtros que la página principal
    filtros = {
        'servicio': request.args.get('servicio'),
        'ip': request.args.get('ip'),
        'fecha_inicio': request.args.get('fecha_inicio'),
        'fecha_fin': request.args.get('fecha_fin'),
        'keyword': request.args.get('keyword')
    }
    
    # Obtener todos los eventos que coinciden con los filtros (sin paginación)
    eventos, _ = obtener_eventos(filtros, page=1, per_page=10000)  # Límite alto para exportar todos
    
    if formato == 'json':
        # Exportar como JSON
        response = make_response(json.dumps(eventos, default=str, indent=4))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = 'attachment; filename=logs_export.json'
        return response
    else:
        # Exportar como CSV (formato por defecto)
        si = StringIO()
        csv_writer = csv.writer(si)
        
        # Escribir cabeceras
        if eventos:
            csv_writer.writerow(eventos[0].keys())
            
            # Escribir filas de datos
            for evento in eventos:
                csv_writer.writerow(evento.values())
        
        output = si.getvalue()
        si.close()
        
        response = make_response(output)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=logs_export.csv'
        return response

@app.route("/reportes")
def reportes():
    """
    Ruta para mostrar reportes estadísticos de acceso.
    
    Presenta datos agregados sobre accesos, incluyendo conteos diarios,
    IPs únicas y errores para facilitar el análisis de tendencias.
    
    Returns:
        str: Renderiza la plantilla reportes.html con estadísticas de acceso
             o la plantilla error.html en caso de error
    """
    try:
        registros_acceso = get_all_registros_acceso()
        
        # Preparar datos para gráficos
        fechas = []
        accesos = []
        errores = []
        
        # Organizar datos para el gráfico (invertimos para orden cronológico)
        for registro in reversed(registros_acceso):
            fechas.append(registro['fecha'].strftime('%d-%m-%Y') if hasattr(registro['fecha'], 'strftime') else registro['fecha'])
            accesos.append(registro['total_accesos'])
            errores.append(registro['errores'])
            
        datos_grafico = {
            'fechas': fechas,
            'accesos': accesos,
            'errores': errores
        }
        
        return render_template(
            "reportes.html", 
            registros_acceso=registros_acceso, 
            datos_grafico=datos_grafico,
            filtros=get_empty_filters()
        )
    except Exception as e:
        return render_template("error.html", error=str(e), filtros=get_empty_filters()), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """
    Manejador para errores 404 (página no encontrada).
    
    Args:
        e: Objeto de error recibido del sistema
        
    Returns:
        tuple: Plantilla error.html y código de estado 404
    """
    return render_template("error.html", error="Página no encontrada", filtros=get_empty_filters()), 404

@app.errorhandler(500)
def internal_server_error(e):
    """
    Manejador para errores 500 (error interno del servidor).
    
    Args:
        e: Objeto de error recibido del sistema
        
    Returns:
        tuple: Plantilla error.html y código de estado 500
    """
    return render_template("error.html", error="Error interno del servidor", filtros=get_empty_filters()), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
