# app/models/renda_movimento_model.py
from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class RendaMovimento(db.Model):
    __tablename__ = 'renda_movimento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    renda_id = db.Column(db.Integer, db.ForeignKey('renda.id'), nullable=False)
    mes_ref = db.Column(db.Date, nullable=False)
    mes_pagto = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('renda_movimentos', lazy=True))
    renda_item = db.relationship('Renda', backref=db.backref('movimentos', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'renda_id', 'mes_ref', 'mes_pagto', name='_usuario_renda_movimento_uc'),
    )

    def __repr__(self):
        return f"<RendaMovimento Renda: {self.renda_id} - {self.mes_ref.strftime('%m/%Y')} - R${self.valor}>"
