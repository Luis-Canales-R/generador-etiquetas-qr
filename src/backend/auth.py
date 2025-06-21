from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import re # Para validación de email

from .models import db, Usuario, UserRole

auth_bp = Blueprint('auth_bp', __name__)

# Helper para validar email
def is_valid_email(email):
    # Expresión regular simple para validación de email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    nombre_completo = data.get('nombre_completo')
    email = data.get('email')
    password = data.get('password')
    rol_str = data.get('rol', 'EMPLEADO') # Default a Empleado si no se especifica

    if not all([nombre_completo, email, password]):
        return jsonify({"message": "Faltan campos requeridos (nombre_completo, email, password)"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Formato de email inválido"}), 400

    if len(password) < 8:
        return jsonify({"message": "La contraseña debe tener al menos 8 caracteres"}), 400

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"message": "El email ya está registrado"}), 409

    try:
        # Convertir string del rol a Enum UserRole
        rol_enum = UserRole[rol_str.upper()]
    except KeyError:
        return jsonify({"message": f"Rol '{rol_str}' inválido. Roles válidos: {', '.join([r.name for r in UserRole])}"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    nuevo_usuario = Usuario(
        nombre_completo=nombre_completo,
        email=email,
        password_hash=hashed_password,
        rol=rol_enum
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        # Opcional: loguear al usuario inmediatamente después del registro
        # login_user(nuevo_usuario)
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "user": {
                "id": nuevo_usuario.id,
                "nombre_completo": nuevo_usuario.nombre_completo,
                "email": nuevo_usuario.email,
                "rol": nuevo_usuario.rol.value
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al registrar el usuario", "error": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Faltan email o contraseña"}), 400

    user = Usuario.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Credenciales inválidas"}), 401

    login_user(user) # El parámetro remember=True se puede añadir si se desea
    return jsonify({
        "message": "Login exitoso",
        "user": {
            "id": user.id,
            "nombre_completo": user.nombre_completo,
            "email": user.email,
            "rol": user.rol.value
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required # Asegura que solo usuarios logueados puedan desloguearse
def logout():
    logout_user()
    return jsonify({"message": "Logout exitoso"}), 200

@auth_bp.route('/status', methods=['GET'])
# No requiere @login_required aquí, para que pueda ser consultado por el frontend
# y determinar si mostrar login o contenido de usuario.
def status():
    if current_user.is_authenticated:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": current_user.id,
                "nombre_completo": current_user.nombre_completo,
                "email": current_user.email,
                "rol": current_user.rol.value
            }
        }), 200
    else:
        return jsonify({"logged_in": False}), 200 # Devolver 200 OK con logged_in: False
