from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

views_bp = Blueprint('views_bp', __name__)

@views_bp.route('/auth/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('views_bp.home'))
    return render_template('auth/login.html')

@views_bp.route('/auth/register', methods=['GET'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('views_bp.home'))
    return render_template('auth/register.html')

@views_bp.route('/')
@login_required # Proteger la página principal
def home():
    # Esta será la página principal o dashboard para usuarios autenticados.
    # Por ahora, una simple bienvenida.
    # Podríamos crear un layout.html base y extenderlo.
    return render_template('dashboard.html', user=current_user)

# Crear una plantilla simple para el dashboard
@views_bp.route('/dashboard') # Ruta alternativa o principal post-login
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)
