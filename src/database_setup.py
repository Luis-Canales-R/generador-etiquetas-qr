from flask import Flask
from src.backend.models import db  # Importa la instancia de db
# Importa todos los modelos para que SQLAlchemy los conozca al crear las tablas
from src.backend.models import Usuario, Ubicacion, Compra, Activo, Mantenimiento, HistorialMovimiento, Auditoria, AuditoriaDetalle

def create_tables(app: Flask):
    """
    Crea todas las tablas en la base de datos dentro del contexto de la aplicación Flask.
    """
    with app.app_context():
        db.create_all()
    print("Tablas creadas (si no existían ya).")

if __name__ == '__main__':
    # Esto es solo para prueba o ejecución directa del script.
    # En la aplicación real, se llamaría desde el contexto de la app Flask.

    # Para ejecutar esto directamente, necesitaríamos una instancia de app configurada mínimamente.
    # Sin embargo, la idea es que este script sea llamado por un comando de Flask
    # o al inicializar la aplicación principal.

    # Ejemplo de cómo podría usarse con un comando Flask CLI (ver app.py para la implementación del comando)
    print("Este script está pensado para ser usado con un comando Flask CLI como 'flask create-db'")
    print("o ser llamado desde la configuración inicial de tu aplicación Flask.")

    # Si quisieras ejecutarlo standalone para crear una BD de prueba (requiere config de app):
    # from src.backend.app import app # Suponiendo que app.py tiene la config de SQLAlchemy
    # create_tables(app)
