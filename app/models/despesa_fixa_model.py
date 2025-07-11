# app/models/despesa_fixa_model.py
from app import db
from sqlalchemy import UniqueConstraint

class DespesaFixa(db.Model):
    __tablename__ = 'despesa_fixa'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    despesa_receita_id = db.Column(db.Integer, db.ForeignKey('despesa_receita.id'), nullable=False)
    mes_ano = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('despesas_fixas', lazy=True))
    despesa_receita_item = db.relationship('DespesaReceita', backref=db.backref('despesas_fixas', lazy=True))

    __table_args__ = (
        UniqueConstraint('usuario_id', 'despesa_receita_id', 'mes_ano', name='_usuario_despesa_fixa_uc'),
    )

    def __repr__(self):
        return f"<DespesaFixa {self.despesa_receita_id} - {self.mes_ano.strftime('%m/%Y')} - R${self.valor}>"
