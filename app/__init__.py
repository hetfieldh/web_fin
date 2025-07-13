from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
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

    # IMPORTAR BLUEPRINTS
    from app.routes.usuario_routes import usuario_bp
    from app.routes.conta_routes import conta_bp
    from app.routes.conta_transacao_routes import conta_transacao_bp
    from app.routes.configuracoes_routes import configuracoes_bp
    from app.routes.dashboard_routes import dashboard_bp 
    from app.routes.crediario_routes import crediario_bp
    from app.routes.crediario_grupo_routes import crediario_grupo_bp
    from app.routes.renda_routes import renda_bp
    from app.routes.despesa_receita_routes import despesa_receita_bp
    from app.routes.despesa_fixa_routes import despesa_fixa_bp
    from app.routes.audit_log_routes import audit_log_bp
    from app.routes.conta_movimento_routes import conta_movimento_bp

    # REGISTRAR BLUEPRINTS
    app.register_blueprint(usuario_bp, url_prefix='/usuarios')
    app.register_blueprint(conta_bp, url_prefix='/contas')
    app.register_blueprint(conta_transacao_bp, url_prefix='/tipos_transacao')
    app.register_blueprint(configuracoes_bp, url_prefix='/configuracoes')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard') 
    app.register_blueprint(crediario_bp, url_prefix='/crediarios')
    app.register_blueprint(crediario_grupo_bp, url_prefix='/crediario_grupos')
    app.register_blueprint(renda_bp, url_prefix='/rendas')
    app.register_blueprint(despesa_receita_bp, url_prefix='/despesa_receita')
    app.register_blueprint(despesa_fixa_bp, url_prefix='/despesas_fixas')
    app.register_blueprint(audit_log_bp, url_prefix='/audit_logs')
    app.register_blueprint(conta_movimento_bp, url_prefix='/conta_movimentos')

    # Rota raiz para redirecionar para o login ou para a página inicial padrão
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for(current_user.default_homepage)) 
        return redirect(url_for('usuario_bp.login'))

    return app

def init_db():
    app = create_app()
    with app.app_context():
        # Importe todos os modelos para que db.create_all() os detecte
        import app.models.usuario_model
        import app.models.conta_model
        import app.models.conta_transacao_model
        import app.models.crediario_model
        import app.models.crediario_grupo_model
        import app.models.renda_model
        import app.models.despesa_receita_model
        import app.models.despesa_fixa_model
        import app.models.audit_log_model
        import app.models.conta_movimento_model
        db.create_all()
        print("Tabelas do banco de dados criadas/verificadas.")

