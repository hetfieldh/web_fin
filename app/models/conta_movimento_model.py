# app/models/conta_movimento_model.py
from app import db
from datetime import datetime

class ContaMovimento(db.Model):
    __tablename__ = 'conta_movimento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    conta_transacao_id = db.Column(db.Integer, db.ForeignKey('conta_transacao.id'), nullable=False)
    data = db.Column(db.Date, nullable=False) # Data do movimento
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

    usuario = db.relationship('Usuario', backref=db.backref('conta_movimentos', lazy=True))
    conta = db.relationship('Conta', backref=db.backref('movimentos', lazy=True))
    conta_transacao_item = db.relationship('ContaTransacao', backref=db.backref('movimentos', lazy=True))

    def __repr__(self):
        return f"<ContaMovimento {self.id} - Conta: {self.conta_id} - Valor: {self.valor}>"
