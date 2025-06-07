from flask import Flask, jsonify, send_from_directory, send_file, request # <-- 'request' es nuevo
import sqlite3
import qrcode
from io import BytesIO

app = Flask(__name__)

# --- La función de conexión a la BD se queda igual ---
def get_db_connection():
    conn = sqlite3.connect('../../data/products.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- La API de productos AHORA MANEJA GET Y POST ---
@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    conn = get_db_connection()
    if request.method == 'GET':
        products_cursor = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
        products_list = [dict(row) for row in products_cursor]
        conn.close()
        return jsonify(products_list)
    
    if request.method == 'POST':
        # Obtenemos los datos enviados desde el frontend
        new_product = request.get_json()
        try:
            conn.execute('INSERT INTO products (product_name, inventory_number) VALUES (?, ?)',
                         (new_product['product_name'], new_product['inventory_number']))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Producto añadido'}), 201
        except sqlite3.IntegrityError:
            # Esto ocurre si el inventory_number ya existe (es UNIQUE)
            conn.close()
            return jsonify({'status': 'error', 'message': 'El ID de inventario ya existe'}), 409

# --- ¡NUEVA RUTA PARA ELIMINAR UN PRODUCTO! ---
@app.route('/api/products/<inventory_number>', methods=['DELETE'])
def delete_product(inventory_number):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE inventory_number = ?', (inventory_number,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Producto eliminado'})

# --- La API de QR se queda igual ---
@app.route('/api/qr/<inventory_number>')
def generate_qr(inventory_number):
    img_buffer = BytesIO()
    qr_img = qrcode.make(inventory_number)
    qr_img.save(img_buffer, 'PNG')
    img_buffer.seek(0)
    return send_file(img_buffer, mimetype='image/png')
    
# --- Las rutas para servir el frontend se quedan igual ---
@app.route('/<path:path>')
def serve_frontend_files(path):
    return send_from_directory('../frontend', path)

@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)