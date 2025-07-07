# app/models/conta_transacao_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

# Defina o ENUM para os tipos de natureza da transação (Crédito/Débito)
# Certifique-se de que o nome 'natureza_transacao_enum' seja o mesmo no banco de dados
natureza_transacao_enum = PG_ENUM('Crédito', 'Débito', name='natureza_transacao', create_type=True)

class ContaTransacao(db.Model):
    __tablename__ = 'conta_transacao'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    transacao = db.Column(db.String(100), nullable=False) # Nome do tipo de transação (e.g., Pix, TED)
    tipo = db.Column(natureza_transacao_enum, nullable=False) # Natureza (Crédito ou Débito)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    # Relacionamento com o modelo Usuario
    usuario = db.relationship('Usuario', backref=db.backref('tipos_transacao', lazy=True))

    # Índice único combinado
    __table_args__ = (
        UniqueConstraint('usuario_id', 'transacao', 'tipo', name='_usuario_transacao_tipo_uc'),
    )

    def __repr__(self):
        return f"<ContaTransacao {self.transacao} ({self.tipo})>"

