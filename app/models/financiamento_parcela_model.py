# app/models/financiamento_parcela_model.py
from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

status_parcela_enum = PG_ENUM('A Pagar', 'Paga', 'Atrasada', 'Amortizada',
                              name='status_parcela', create_type=True)

class FinanciamentoParcela(db.Model):
    __tablename__ = 'financiamento_parcela'

    id = db.Column(db.Integer, primary_key=True)
    financiamento_id = db.Column(db.Integer, db.ForeignKey('financiamento.id'), nullable=False)
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor_principal = db.Column(db.Numeric(12, 2), nullable=False)
    valor_juros = db.Column(db.Numeric(12, 2), nullable=False)
    valor_seguro = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    valor_taxas = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    valor_total_previsto = db.Column(db.Numeric(12, 2), nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True) # Nulo por padrão
    valor_pago = db.Column(db.Numeric(12, 2), nullable=True) # Nulo por padrão
    status = db.Column(status_parcela_enum, nullable=False, default='A Pagar')
    observacoes = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relacionamento com o modelo Financiamento
    financiamento = db.relationship('Financiamento', backref=db.backref('parcelas', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint('financiamento_id', 'numero_parcela', name='_financiamento_parcela_uc'),
    )

    def __repr__(self):
        return f"<FinanciamentoParcela Financiamento: {self.financiamento_id} - Parcela: {self.numero_parcela}>"
