# app/models/conta_transacao_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

tipo_natureza_transacao_enum = PG_ENUM('Crédito', 'Débito', name='natureza_transacao', create_type=True)

class ContaTransacao(db.Model):
    __tablename__ = 'conta_transacao'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    transacao = db.Column(db.String(100), nullable=False)
    tipo = db.Column(tipo_natureza_transacao_enum, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('tipos_transacao', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'transacao', 'tipo', name='_usuario_transacao_tipo_uc'),
    )

    def __repr__(self):
        return f"<ContaTransacao {self.transacao} ({self.tipo})>"
