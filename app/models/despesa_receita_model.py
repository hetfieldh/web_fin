# app/models/despesa_receita_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

tipo_despesa_receita_enum = PG_ENUM('Receita', 'Despesa',
                                    name='tipo_despesa_receita', create_type=True)

class DespesaReceita(db.Model):
    __tablename__ = 'despesa_receita'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    despesa_receita = db.Column(db.String(100), nullable=False)
    tipo = db.Column(tipo_despesa_receita_enum, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('despesas_receitas', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'despesa_receita', 'tipo', name='_usuario_despesa_receita_uc'),
    )

    def __repr__(self):
        return f"<DespesaReceita {self.despesa_receita} ({self.tipo})>"
