from app import db, login_manager
from flask_login import UserMixin

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    login = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Usuario {self.login}>"

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))