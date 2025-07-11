# app/models/crediario_model.py
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import UniqueConstraint

# Define o ENUM para os tipos de crediário
# Certifique-se de que o nome 'tipo_crediario' seja o mesmo no banco de dados
tipo_crediario_enum = PG_ENUM('Físico', 'Virtual Recorrente', 'Virtual Temporário', 'Outro',
                              name='tipo_crediario', create_type=True)

class Crediario(db.Model):
    __tablename__ = 'crediario'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    crediario = db.Column(db.String(100), nullable=False) # Nome do crediário
    tipo = db.Column(tipo_crediario_enum, nullable=False)
    final = db.Column(db.String(20), nullable=True) # Ex: final do cartão, nome do estabelecimento
    limite = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    descricao = db.Column(db.String(255), nullable=True)

    # Relacionamento com o modelo Usuario
    usuario = db.relationship('Usuario', backref=db.backref('crediarios', lazy=True))

    # Índice único combinado
    __table_args__ = (
        UniqueConstraint('usuario_id', 'crediario', 'tipo', 'final', name='_usuario_crediario_uc'),
    )

    def __repr__(self):
        return f"<Crediario {self.crediario} ({self.tipo})>"

