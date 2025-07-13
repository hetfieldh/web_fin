# app/models/crediario_movimento_model.py
from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class CrediarioMovimento(db.Model):
    __tablename__ = 'crediario_movimento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    crediario_id = db.Column(db.Integer, db.ForeignKey('crediario.id'), nullable=False)
    crediario_grupo_id = db.Column(db.Integer, db.ForeignKey('crediario_grupo.id'), nullable=False)
    data_compra = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    valor_total = db.Column(db.Numeric(12, 2), nullable=False)
    num_parcelas = db.Column(db.Integer, nullable=False)
    primeira_parcela = db.Column(db.Date, nullable=False)
    ultima_parcela = db.Column(db.Date, nullable=False)
    valor_parcela_mensal = db.Column(db.Numeric(12, 2), nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    usuario = db.relationship('Usuario', backref=db.backref('crediario_movimentos', lazy=True))
    crediario = db.relationship('Crediario', backref=db.backref('movimentos', lazy=True))
    crediario_grupo = db.relationship('CrediarioGrupo', backref=db.backref('movimentos', lazy=True))

    # Índice único combinado
    __table_args__ = (
        UniqueConstraint('usuario_id', 'crediario_grupo_id', 'crediario_id', 'data_compra', 'descricao', 'valor_total', name='_usuario_crediario_movimento_uc'),
    )

    def __repr__(self):
        return f"<CrediarioMovimento {self.id} - Crediário: {self.crediario_id} - Valor: {self.valor_total}>"
