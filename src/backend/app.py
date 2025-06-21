import os
from flask import Flask, jsonify, send_from_directory, send_file, request, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from pathlib import Path
import qrcode # Manteniendo qrcode por si se usa más adelante
from io import BytesIO

# --- Modelos y Configuración de DB ---
from .models import db, Usuario # Importamos db y Usuario para el LoginManager
# No importamos todos los modelos aquí para evitar importaciones circulares si ellos importan 'app'
# Se importarán donde se necesiten o en database_setup.py

# --- Rutas inteligentes para encontrar siempre los archivos ---
BASE_DIR = Path(__file__).resolve().parent
# FRONTEND_FOLDER sigue apuntando a src/frontend para los archivos estáticos del panel admin original
FRONTEND_FOLDER = BASE_DIR.parent / 'frontend'
# TEMPLATE_FOLDER ahora apunta a src/backend/templates para las plantillas de Flask (auth, etc.)
TEMPLATE_FOLDER = BASE_DIR / 'templates'
# Carpeta para la base de datos SQLite
DATA_DIR = BASE_DIR.parent.parent / 'data'
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

# --- Configuración de Flask ---
app = Flask(__name__, static_folder=str(FRONTEND_FOLDER), template_folder=str(TEMPLATE_FOLDER))
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'una-clave-secreta-muy-segura-debe-cambiarse') # Cambiar en producción
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATA_DIR / 'sga.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialización de Extensiones ---
db.init_app(app)
migrate = Migrate(app, db) # Para migraciones de base de datos
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'views_bp.login_page' # CORREGIDO: Apunta a la vista que renderiza la página de login
login_manager.login_message_category = "info" # Categoría para mensajes flash

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- Blueprints ---
# (Se crearán los archivos auth.py y views.py más adelante)
from .auth import auth_bp # Lo crearemos después
app.register_blueprint(auth_bp, url_prefix='/api/auth')

from .views import views_bp # Lo crearemos después
app.register_blueprint(views_bp) # Sin prefijo para rutas como /login, /register


# --- Comandos CLI de Flask ---
@app.cli.command("create-db")
def create_db_command():
    """Crea las tablas de la base de datos."""
    from src.database_setup import create_tables # Importación local para el comando
    create_tables(app)
    print("Comando create-db ejecutado.")

# --- Rutas de la API (Antiguas - a ser revisadas/integradas/eliminadas) ---
# Estas rutas interactúan con la antigua estructura de 'products.db' y sqlite3 directamente.
# Deberán ser adaptadas para usar SQLAlchemy y los nuevos modelos (ej. 'Activo') o eliminadas si ya no son relevantes.

# Mantenemos la conexión directa a la antigua DB por ahora para no romper el frontend existente inmediatamente.
# Idealmente, esto se migraría o se eliminaría.
OLD_DB_PATH = BASE_DIR.parent.parent / 'data' / 'products.db'

def get_old_db_connection():
    # Solo conectar si el archivo de la BD antigua existe
    if not OLD_DB_PATH.exists():
        return None
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    # Esta ruta interactúa con la antigua base de datos 'products.db'
    # Deberá ser actualizada o reemplazada por la lógica de 'activos' del nuevo sistema
    conn = get_old_db_connection()
    if not conn:
        return jsonify({"error": "Antigua base de datos no encontrada"}), 500

    if request.method == 'GET':
        try:
            products_cursor = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
            products_list = [dict(row) for row in products_cursor]
        except sqlite3.Error as e:
            return jsonify({"error": f"Error en la base de datos antigua: {e}"}), 500
        finally:
            conn.close()
        return jsonify(products_list)
    
    if request.method == 'POST':
        # Esto debería migrarse para crear 'Activos' en la nueva BD
        return jsonify({'status': 'warning', 'message': 'Esta funcionalidad debe migrarse al nuevo sistema de activos.'}), 400

@app.route('/api/products/<inventory_number>', methods=['DELETE'])
def delete_product(inventory_number):
    # Esta ruta también debería migrarse
    return jsonify({'status': 'warning', 'message': 'Esta funcionalidad debe migrarse al nuevo sistema de activos.'}), 400

@app.route('/api/qr/<inventory_number>')
def generate_qr(inventory_number):
    # Esta ruta podría adaptarse para generar QR para 'Activos' usando 'codigo_activo'
    # La URL codificada también debería apuntar a la nueva vista de detalles del activo.
    # Por ahora, la dejamos apuntando a la ruta antigua para no romper el frontend si aún se usa.
    # ¡URL actualizada con tu dirección IP local!
    # ESTO DEBE SER CONFIGURABLE O DETECTADO AUTOMATICAMENTE
    # url_to_encode = f"http://192.168.1.144:5000/product/{inventory_number}" # Ruta antigua
    url_to_encode = f"http://127.0.0.1:5000/asset/view/{inventory_number}" # Ejemplo de nueva ruta (a crear)
    
    img_buffer = BytesIO()
    qr_img = qrcode.make(url_to_encode)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')
        
@app.route('/product/<inventory_number>') # Antigua ruta de detalle
def product_detail_page(inventory_number):
    # Esta vista HTML también debería migrarse para mostrar detalles de un 'Activo'
    # y usar la nueva plantilla y sistema de BD.
    conn = get_old_db_connection()
    if not conn:
        return "Antigua base de datos no encontrada", 404
    try:
        product = conn.execute('SELECT * FROM products WHERE inventory_number = ?',
                               (inventory_number,)).fetchone()
    except sqlite3.Error as e:
        return f"Error en la base de datos antigua: {e}", 500
    finally:
        conn.close()

    if product is None:
        return "Producto no encontrado en la base de datos antigua", 404

    # Asumiendo que 'src/backend/templates/product_detail.html' es la plantilla antigua.
    # Si esta plantilla se movió o renombró, ajustar aquí.
    # La configuración de TEMPLATE_FOLDER es ahora src/backend/templates
    # Si la plantilla product_detail.html está en la raíz de esa carpeta, esto debería funcionar.
    return render_template('product_detail.html', product=dict(product))


# --- Rutas para servir el Panel de Administración (Frontend Estático Original) ---
# Estas rutas sirven los archivos de 'src/frontend' (HTML, JS, CSS del panel original)
@app.route('/admin/<path:path>') # Añadido /admin para diferenciar del nuevo frontend de Flask
def serve_frontend_files(path):
    return send_from_directory(FRONTEND_FOLDER, path)

@app.route('/admin/') # Añadido /admin
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    # Usamos host='0.0.0.0' para que el servidor sea accesible en tu red local
    # El puerto 5000 es el default de Flask.
    app.run(host='0.0.0.0', port=5000, debug=True)