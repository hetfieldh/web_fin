from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    load_dotenv(encoding='utf-8') 

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'usuario_bp.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    from app.routes.usuario_routes import usuario_bp
    app.register_blueprint(usuario_bp)

    return app

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        import app.models.usuario_model
        print("Tabelas do banco de dados criadas/verificadas.")