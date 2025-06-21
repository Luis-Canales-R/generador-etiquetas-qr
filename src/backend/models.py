import enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

db = SQLAlchemy()

# --- Enums ---
class AssetStatus(enum.Enum):
    EN_BODEGA = "En Bodega"
    ACTIVO = "Activo"
    EN_REPARACION = "En Reparación"
    EN_PRESTAMO = "En Préstamo"
    DADO_DE_BAJA = "Dado de Baja"

class UserRole(enum.Enum):
    ADMIN = "Admin"
    TECNICO = "Técnico"
    CONTADOR = "Contador"
    AUDITOR = "Auditor"
    EMPLEADO = "Empleado"

class MaintenanceType(enum.Enum):
    PREVENTIVO = "Preventivo"
    CORRECTIVO = "Correctivo"
    MEJORA = "Mejora"
    DIAGNOSTICO = "Diagnóstico"

class AuditStatus(enum.Enum):
    EN_PROGRESO = "En Progreso"
    COMPLETADA = "Completada"
    CANCELADA = "Cancelada"

class ScanResult(enum.Enum):
    OK = "OK"
    UBICACION_INCORRECTA = "Ubicación Incorrecta"
    NO_ENCONTRADO = "No Encontrado"
    ACTIVO_DESCONOCIDO = "Activo Desconocido"

# --- Modelos de Tablas ---

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False) # Ajustado para reflejar el plan
    rol = Column(Enum(UserRole), nullable=False)

    # Relaciones inversas
    activos_asignados = relationship("Activo", back_populates="usuario_asignado", foreign_keys="Activo.usuario_asignado_id")
    activos_auditados_por = relationship("Activo", back_populates="ultima_auditoria_por", foreign_keys="Activo.ultima_auditoria_por_id")
    compras_solicitadas = relationship("Compra", back_populates="solicitado_por")
    mantenimientos_realizados = relationship("Mantenimiento", back_populates="realizado_por")
    historial_cambios = relationship("HistorialMovimiento", back_populates="usuario")
    auditorias_realizadas = relationship("Auditoria", back_populates="auditor")

    def __repr__(self):
        return f"<Usuario {self.email}>"

class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False, unique=True)
    descripcion = Column(Text)
    parent_ubicacion_id = Column(Integer, ForeignKey('ubicaciones.id'), nullable=True)

    # Relaciones
    parent_ubicacion = relationship("Ubicacion", remote_side=[id], backref="sub_ubicaciones")
    activos = relationship("Activo", back_populates="ubicacion")
    auditorias_en_ubicacion = relationship("Auditoria", back_populates="ubicacion_auditada")

    def __repr__(self):
        return f"<Ubicacion {self.nombre}>"

class Compra(db.Model):
    __tablename__ = 'compras'
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_factura = Column(String(100))
    proveedor = Column(String(255))
    fecha_compra = Column(Date, nullable=False)
    solicitado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    solicitado_por = relationship("Usuario", back_populates="compras_solicitadas")
    activos = relationship("Activo", back_populates="compra")

    def __repr__(self):
        return f"<Compra ID: {self.id}, Factura: {self.numero_factura}>"

class Activo(db.Model):
    __tablename__ = 'activos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_activo = Column(String(50), unique=True, nullable=False)
    nombre_activo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(100), unique=True, nullable=True) # Puede ser null si no aplica
    status = Column(Enum(AssetStatus), default=AssetStatus.EN_BODEGA)

    fecha_adquisicion = Column(Date, nullable=False)
    costo_adquisicion = Column(Numeric(10, 2), nullable=False)
    vida_util_meses = Column(Integer, nullable=False, default=36)
    valor_residual = Column(Numeric(10, 2), nullable=False, default=0)

    ubicacion_id = Column(Integer, ForeignKey('ubicaciones.id'))
    usuario_asignado_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    compra_id = Column(Integer, ForeignKey('compras.id'))

    ultima_auditoria_fecha = Column(DateTime(timezone=True), nullable=True)
    ultima_auditoria_por_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    ubicacion = relationship("Ubicacion", back_populates="activos")
    usuario_asignado = relationship("Usuario", back_populates="activos_asignados", foreign_keys=[usuario_asignado_id])
    compra = relationship("Compra", back_populates="activos")
    ultima_auditoria_por = relationship("Usuario", back_populates="activos_auditados_por", foreign_keys=[ultima_auditoria_por_id])

    mantenimientos = relationship("Mantenimiento", back_populates="activo", cascade="all, delete-orphan")
    historial_movimientos = relationship("HistorialMovimiento", back_populates="activo", cascade="all, delete-orphan")
    detalles_auditoria = relationship("AuditoriaDetalle", back_populates="activo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Activo {self.codigo_activo} ({self.nombre_activo})>"

class Mantenimiento(db.Model):
    __tablename__ = 'mantenimientos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    activo_id = Column(Integer, ForeignKey('activos.id'), nullable=False)
    fecha_mantenimiento = Column(Date, nullable=False)
    tipo_mantenimiento = Column(Enum(MaintenanceType))
    descripcion = Column(Text, nullable=False)
    costo = Column(Numeric(10, 2), default=0)
    realizado_por_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)

    # Relaciones
    activo = relationship("Activo", back_populates="mantenimientos")
    realizado_por = relationship("Usuario", back_populates="mantenimientos_realizados")

    def __repr__(self):
        return f"<Mantenimiento ID: {self.id} para Activo ID: {self.activo_id}>"

class HistorialMovimiento(db.Model):
    __tablename__ = 'historial_movimientos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    activo_id = Column(Integer, ForeignKey('activos.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False) # Quién hizo el cambio
    fecha_cambio = Column(DateTime(timezone=True), server_default=func.now())
    campo_modificado = Column(String(100))
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    nota = Column(Text)

    # Relaciones
    activo = relationship("Activo", back_populates="historial_movimientos")
    usuario = relationship("Usuario", back_populates="historial_cambios")

    def __repr__(self):
        return f"<Historial ID: {self.id} para Activo ID: {self.activo_id}>"

class Auditoria(db.Model):
    __tablename__ = 'auditorias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ubicacion_auditada_id = Column(Integer, ForeignKey('ubicaciones.id'), nullable=False)
    auditor_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AuditStatus), default=AuditStatus.EN_PROGRESO)
    resumen = Column(Text)

    # Relaciones
    ubicacion_auditada = relationship("Ubicacion", back_populates="auditorias_en_ubicacion")
    auditor = relationship("Usuario", back_populates="auditorias_realizadas")
    detalles = relationship("AuditoriaDetalle", back_populates="auditoria", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Auditoria ID: {self.id} en Ubicacion ID: {self.ubicacion_auditada_id}>"

class AuditoriaDetalle(db.Model):
    __tablename__ = 'auditoria_detalles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    auditoria_id = Column(Integer, ForeignKey('auditorias.id'), nullable=False)
    activo_id = Column(Integer, ForeignKey('activos.id'), nullable=False)
    resultado = Column(Enum(ScanResult), nullable=False)
    timestamp_scan = Column(DateTime(timezone=True), server_default=func.now())
    nota = Column(Text)

    # Relaciones
    auditoria = relationship("Auditoria", back_populates="detalles")
    activo = relationship("Activo", back_populates="detalles_auditoria")

    def __repr__(self):
        return f"<AuditoriaDetalle ID: {self.id} para Auditoria ID: {self.auditoria_id}, Activo ID: {self.activo_id}>"
