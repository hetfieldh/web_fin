# app/models/financiamento_model.py
from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

tipo_amortizacao_enum = PG_ENUM('SAC', 'PRICE', 'Outro',
                                name='tipo_amortizacao', create_type=True)

class Financiamento(db.Model):
    __tablename__ = 'financiamento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    nome_financiamento = db.Column(db.String(100), nullable=False)
    valor_total_financiado = db.Column(db.Numeric(12, 2), nullable=False)
    taxa_juros_anual = db.Column(db.Numeric(5, 4), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    prazo_meses = db.Column(db.Integer, nullable=False)
    tipo_amortizacao = db.Column(tipo_amortizacao_enum, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    usuario = db.relationship('Usuario', backref=db.backref('financiamentos', lazy=True))
    conta = db.relationship('Conta', backref=db.backref('financiamentos', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'nome_financiamento', name='_usuario_financiamento_uc'),
    )

    def __repr__(self):
        return f"<Financiamento {self.nome_financiamento} - R${self.valor_total_financiado}>"
