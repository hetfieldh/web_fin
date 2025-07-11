# app/models/crediario_grupo_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

tipo_grupo_crediario_enum = PG_ENUM('Compra', 'Estorno',
                                    name='tipo_grupo_crediario', create_type=True)

class CrediarioGrupo(db.Model):
    __tablename__ = 'crediario_grupo'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo = db.Column(db.String(100), nullable=False)
    tipo = db.Column(tipo_grupo_crediario_enum, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('crediario_grupos', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'grupo', 'tipo', name='_usuario_grupo_crediario_uc'),
    )

    def __repr__(self):
        return f"<CrediarioGrupo {self.grupo} ({self.tipo})>"
