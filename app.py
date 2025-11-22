# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import init_neo4j, close_driver # Importamos nuestro nuevo conector
import atexit # Para cerrar la conexión al apagar la app

# Importar Blueprints
# from routes.articulos import articulos_bp
# from routes.categoria_articulos import categoria_articulos_bp
# from routes.categorias import categorias_bp
# from routes.comentarios import comentarios_bp
# from routes.tag_articulos import tag_articulos_bp
# from routes.tags import tags_bp
from routes.usuarios import usuarios_bp

from URI import URI, USER, PASSWORD

app = Flask(__name__)
CORS(app)

# --- 1. Inicializar Neo4j ---
try:
    # Conectar a AuraDB
    init_neo4j(URI, USER, PASSWORD)
    print("Conexión a Neo4j Aura exitosa.")
except Exception as e:
    print(f"Error conectando a Neo4j: {e}")

# Asegurar que el driver se cierre cuando la app se apague
atexit.register(close_driver)

# --- 2. Registrar Blueprints ---
# app.register_blueprint(articulos_bp, url_prefix='/api/articulos')
# app.register_blueprint(categorias_bp, url_prefix='/api/categorias')
# app.register_blueprint(comentarios_bp, url_prefix='/api/comentarios')
# app.register_blueprint(tags_bp, url_prefix='/api/tags')
app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
# app.register_blueprint(categoria_articulos_bp, url_prefix='/api/categoria')
# app.register_blueprint(tag_articulos_bp, url_prefix='/api/tag')

# --- Endpoint de prueba simple para saber que pudimos conectarnos ---
@app.route('/api/debug/connection')
def debug_connection():
    from extensions import get_driver
    driver = get_driver()
    try:
        # Verificamos conectividad con una consulta simple
        driver.verify_connectivity()
        return jsonify({"status": "success", "message": "Conectado al Grafo 🟢"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)