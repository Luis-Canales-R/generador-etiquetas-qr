from flask import Flask, jsonify, send_from_directory, send_file, request
import sqlite3
import qrcode
from io import BytesIO
from pathlib import Path # <-- ¡Importante!

# --- Hacemos las rutas inteligentes ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / 'data' / 'products.db'
FRONTEND_FOLDER = BASE_DIR.parent / 'frontend'
# --- Fin de la sección inteligente ---

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH) # <-- Usamos la ruta inteligente
    conn.row_factory = sqlite3.Row
    return conn
    
# --- El resto de tus rutas no necesitan cambiar ---
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    # ... (el código de esta función no cambia) ...
    conn = get_db_connection()
    if request.method == 'GET':
        products_cursor = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
        products_list = [dict(row) for row in products_cursor]
        conn.close()
        return jsonify(products_list)
    
    if request.method == 'POST':
        new_product = request.get_json()
        try:
            conn.execute('INSERT INTO products (product_name, inventory_number) VALUES (?, ?)',
                         (new_product['product_name'], new_product['inventory_number']))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Producto añadido'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'status': 'error', 'message': 'El ID de inventario ya existe'}), 409

@app.route('/api/products/<inventory_number>', methods=['DELETE'])
def delete_product(inventory_number):
    # ... (el código de esta función no cambia) ...
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE inventory_number = ?', (inventory_number,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Producto eliminado'})

@app.route('/api/qr/<inventory_number>')
def generate_qr(inventory_number):
    # ... (el código de esta función no cambia) ...
    img_buffer = BytesIO()
    qr_img = qrcode.make(inventory_number)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')
    
@app.route('/<path:path>')
def serve_frontend_files(path):
    return send_from_directory(FRONTEND_FOLDER, path) # <-- Usamos la ruta inteligente

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html') # <-- Usamos la ruta inteligente

if __name__ == '__main__':
    app.run(debug=True)