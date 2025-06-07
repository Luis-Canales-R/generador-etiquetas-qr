from flask import Flask, jsonify, send_from_directory, send_file, request
import sqlite3
import qrcode
from io import BytesIO
from pathlib import Path

# --- Rutas inteligentes para encontrar siempre los archivos ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / 'data' / 'products.db'
FRONTEND_FOLDER = BASE_DIR.parent / 'frontend'

# Inicialización de la aplicación Flask
app = Flask(__name__)

# --- Función para conectar a la base de datos ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    
# --- Ruta de la API para obtener (GET) y añadir (POST) productos ---
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    conn = get_db_connection()
    
    # Si la petición es GET, devolvemos la lista de productos
    if request.method == 'GET':
        products_cursor = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
        products_list = [dict(row) for row in products_cursor]
        conn.close()
        return jsonify(products_list)
    
    # =======================================================
    # ===   BLOQUE ACTUALIZADO PARA AÑADIR PRODUCTOS      ===
    # =======================================================
    if request.method == 'POST':
        # Obtenemos el objeto JSON completo enviado desde el frontend
        new_product = request.get_json()
        try:
            # Preparamos la sentencia SQL para insertar todos los campos nuevos
            conn.execute("""
                INSERT INTO products (
                    product_name, inventory_number, serial_number, brand, model, equipment_type
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                new_product['product_name'],
                new_product['inventory_number'],
                new_product.get('serial_number'), # Usamos .get() por si el campo viene vacío
                new_product.get('brand'),
                new_product.get('model'),
                new_product.get('equipment_type')
            ))
            conn.commit()
            conn.close()
            # Devolvemos una respuesta de éxito
            return jsonify({'status': 'success', 'message': 'Producto añadido'}), 201
        except sqlite3.IntegrityError:
            # Esto ocurre si el inventory_number ya existe (es UNIQUE)
            conn.close()
            return jsonify({'status': 'error', 'message': 'El ID de inventario ya existe'}), 409
    # =======================================================
    # ===   FIN DEL BLOQUE ACTUALIZADO                    ===
    # =======================================================

# --- Ruta para eliminar un producto por su ID de inventario ---
@app.route('/api/products/<inventory_number>', methods=['DELETE'])
def delete_product(inventory_number):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE inventory_number = ?', (inventory_number,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Producto eliminado'})

# --- Ruta para generar la imagen del código QR ---
@app.route('/api/qr/<inventory_number>')
def generate_qr(inventory_number):
    img_buffer = BytesIO()
    qr_img = qrcode.make(inventory_number)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')
    
# --- Rutas para servir los archivos del frontend ---
@app.route('/<path:path>')
def serve_frontend_files(path):
    return send_from_directory(FRONTEND_FOLDER, path)

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == '__main__':
    app.run(debug=True)