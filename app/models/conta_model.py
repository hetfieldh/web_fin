# app/models/conta_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

# Defina o ENUM para os tipos de conta
# Certifique-se de que o nome 'tipo_conta' seja o mesmo no banco de dados.
# Se for a primeira vez que você está executando isso, o SQLAlchemy vai criar o tipo no DB
tipo_conta_enum = PG_ENUM('Corrente', 'Poupança', 'Digital', 'Investimento', 'Caixinha', 'Dinheiro',
                          name='tipo_conta', create_type=True)

class Conta(db.Model):
    __tablename__ = 'conta'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nome_banco = db.Column(db.String(100), nullable=False)
    agencia = db.Column(db.String(20), nullable=True) # Pode ser nulo para contas digitais/caixinhas
    conta = db.Column(db.String(50), nullable=False)
    tipo = db.Column(tipo_conta_enum, nullable=False)
    saldo_inicial = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    limite = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    # Relacionamento com o modelo Usuario
    usuario = db.relationship('Usuario', backref=db.backref('contas', lazy=True))

    # Índice único combinado
    __table_args__ = (
        UniqueConstraint('usuario_id', 'nome_banco', 'agencia', 'conta', 'tipo', name='_usuario_conta_uc'),
    )

    def __repr__(self):
        return f"<Conta {self.nome_banco} - {self.conta} ({self.tipo})>"