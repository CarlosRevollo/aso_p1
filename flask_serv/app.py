from flask import Flask, render_template
from database import *

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reportes")
def reportes():
    registros_acceso = get_all_registros_acceso()
    return render_template("reportes.html",registros_acceso = registros_acceso)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)

