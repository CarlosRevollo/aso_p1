import mysql.connector

db_config = {
    "host":"localhost",
    "user":"root",
    "password":"vilfredos",
    "database":"bdlogs"
}
def get_connection():
    return mysql.connector.connect(**db_config)

def get_all_registros_acceso():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ip,fecha_hora from registros_acceso")
    datos = cursor.fetchall()
    cursor.close()
    conn.close()
    return datos