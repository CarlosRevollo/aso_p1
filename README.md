# APP_LOGS - Aplicación de Visualización de Logs

Una aplicación web basada en Flask para la visualización, búsqueda y análisis de logs de servicios como Apache y FTP.

## Características

- Visualización unificada de logs de diferentes servicios (Apache y FTP)
- Filtrado de logs por servicio, dirección IP, fecha y palabras clave
- Reportes estadísticos de acceso a servidores
- Interfaz gráfica fácil de usar con Bootstrap

## Requisitos

- Python 3.12 o superior
- MySQL/MariaDB
- Dependencias de Python especificadas en `requirements.txt`

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/CarlosRevollo/aso_p1
   cd aso_p1
   ```

2. Crea y activa un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate   # En Linux/Mac
   # o
   venv\Scripts\activate      # En Windows
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configura la base de datos:
   - Crea una base de datos llamada `bdlogs` en MySQL/MariaDB
   - Actualiza las credenciales de la base de datos en `app/config.py`
   - Importa el esquema de la base de datos (script no incluido)

## Configuración

El archivo `app/config.py` contiene todas las configuraciones necesarias. Debes modificarlo para adaptarlo a tu entorno:

- `DatabaseConfig`: Configuración de la base de datos (host, usuario, contraseña, etc.)
- `Config`: Configuración general de la aplicación (puerto, modo debug, clave secreta, etc.)

**Importante**: En un entorno de producción, debes cambiar la clave secreta y desactivar el modo debug.

## Ejecución

Para ejecutar la aplicación:

```
cd app
python app.py
```

La aplicación estará disponible en: http://localhost:5000

## Estructura del Proyecto

```
ASO_P1/
├── flask_serv/
│   ├── app.py           # Punto de entrada de la aplicación Flask
│   ├── config.py        # Configuraciones centralizadas
│   ├── database.py      # Funciones de acceso a la base de datos
│   └── templates/       # Plantillas HTML
│       ├── base.html    # Plantilla base con estructura común
│       ├── index.html   # Página principal (visualización de logs)
│       ├── reportes.html # Página de reportes estadísticos
│       └── error.html   # Página de errores
└── requirements.txt     # Dependencias del proyecto
```

## Escalabilidad

La aplicación utiliza un pool de conexiones a la base de datos para mejorar el rendimiento y la escalabilidad en entornos con alta carga de trabajo.

## Mantenimiento

Para agregar soporte para nuevos tipos de logs, se debe:

1. Crear una tabla apropiada en la base de datos
2. Agregar una nueva sección en la función `obtener_eventos()` en `database.py`
3. Actualizar la interfaz para incluir el nuevo servicio en los filtros
