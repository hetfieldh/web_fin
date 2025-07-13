# app/models/crediario_parcela_model.py
from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class CrediarioParcela(db.Model):
    __tablename__ = 'crediario_parcela'

    id = db.Column(db.Integer, primary_key=True)
    crediario_movimento_id = db.Column(db.Integer, db.ForeignKey('crediario_movimento.id'), nullable=False)
    numero_parcela = db.Column(db.Integer, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    valor_parcela = db.Column(db.Numeric(12, 2), nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relacionamento com o modelo CrediarioMovimento
    # Adicionado cascade para excluir parcelas quando a movimentação é excluída
    crediario_movimento = db.relationship('CrediarioMovimento', backref=db.backref('parcelas', lazy=True, cascade="all, delete-orphan"))

    # Índice único combinado
    __table_args__ = (
        UniqueConstraint('crediario_movimento_id', 'numero_parcela', name='_crediario_movimento_parcela_uc'),
    )

    def __repr__(self):
        return f"<CrediarioParcela Movimento: {self.crediario_movimento_id} - Parcela: {self.numero_parcela}>"
