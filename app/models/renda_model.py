# app/models/renda_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

tipo_renda_enum = PG_ENUM('Provento', 'Benefício', 'Desconto', 'Imposto',
                          name='tipo_renda', create_type=True)

class Renda(db.Model):
    __tablename__ = 'renda'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    tipo = db.Column(tipo_renda_enum, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    usuario = db.relationship('Usuario', backref=db.backref('rendas', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'descricao', 'tipo', name='_usuario_renda_uc'),
    )

    def __repr__(self):
        return f"<Renda {self.descricao} ({self.tipo})>"
