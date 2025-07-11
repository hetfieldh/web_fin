# app/models/crediario_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

tipo_crediario_enum = PG_ENUM('Físico', 'Virtual Recorrente', 'Virtual Temporário', 'Outro',
                              name='tipo_crediario', create_type=True)

class Crediario(db.Model):
    __tablename__ = 'crediario'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    crediario = db.Column(db.String(100), nullable=False)
    tipo = db.Column(tipo_crediario_enum, nullable=False)
    final = db.Column(db.String(20), nullable=True)
    limite = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('crediarios', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'crediario', 'tipo', 'final', name='_usuario_crediario_uc'),
    )

    def __repr__(self):
        return f"<Crediario {self.crediario} ({self.tipo})>"
