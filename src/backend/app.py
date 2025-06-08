# Importaciones necesarias, incluyendo 'render_template' para las páginas HTML
from flask import Flask, jsonify, send_from_directory, send_file, request, render_template
import sqlite3
import qrcode
from io import BytesIO
from pathlib import Path

# --- Rutas inteligentes para encontrar siempre los archivos ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / 'data' / 'products.db'
FRONTEND_FOLDER = BASE_DIR.parent / 'frontend'
TEMPLATE_FOLDER = BASE_DIR.parent.parent / 'templates' # Ruta a la nueva carpeta de plantillas

# --- Configuración de Flask ---
# Le decimos a Flask dónde está el frontend (static_folder) y las plantillas (template_folder)
app = Flask(__name__, static_folder=str(FRONTEND_FOLDER), template_folder=str(TEMPLATE_FOLDER))

# --- Función para conectar a la base de datos ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    
# --- Rutas de la API (Sin cambios) ---
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    conn = get_db_connection()
    if request.method == 'GET':
        products_cursor = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
        products_list = [dict(row) for row in products_cursor]
        conn.close()
        return jsonify(products_list)
    
    if request.method == 'POST':
        new_product = request.get_json()
        try:
            conn.execute("""
                INSERT INTO products (
                    product_name, inventory_number, serial_number, brand, model, equipment_type
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                new_product['product_name'], new_product['inventory_number'],
                new_product.get('serial_number'), new_product.get('brand'),
                new_product.get('model'), new_product.get('equipment_type')
            ))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Producto añadido'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'status': 'error', 'message': 'El ID de inventario ya existe'}), 409

@app.route('/api/products/<inventory_number>', methods=['DELETE'])
def delete_product(inventory_number):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE inventory_number = ?', (inventory_number,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Producto eliminado'})

# =======================================================
# =====   GENERACIÓN DE QR CON URL COMPLETA           =====
# =======================================================
@app.route('/api/qr/<inventory_number>')
def generate_qr(inventory_number):
    # ¡URL actualizada con tu dirección IP local!
    url_to_encode = f"http://192.168.1.144:5000/product/{inventory_number}"
    
    img_buffer = BytesIO()
    qr_img = qrcode.make(url_to_encode)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')
        
# =======================================================
# =====   ¡NUEVA RUTA PARA LA PÁGINA DE DETALLES!   =====
# =======================================================
@app.route('/product/<inventory_number>')
def product_detail_page(inventory_number):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE inventory_number = ?', 
                           (inventory_number,)).fetchone()
    conn.close()

    if product is None:
        return "Producto no encontrado", 404

    # Renderizamos la plantilla 'product_detail.html' y le pasamos los datos
    return render_template('product_detail.html', product=dict(product))


# --- Rutas para servir el Panel de Administración (Frontend) ---
@app.route('/<path:path>')
def serve_frontend_files(path):
    return send_from_directory(FRONTEND_FOLDER, path)

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    # Usamos host='0.0.0.0' para que el servidor sea accesible en tu red local
    app.run(host='0.0.0.0', debug=True)