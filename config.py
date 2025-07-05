import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Desativa o rastreamento de modificações do SQLAlchemy (consome menos memória)

    # Configurações de autenticação (Flask-Login)
    REMEMBER_COOKIE_DURATION = 3600 # 1 hora em segundos
    REMEMBER_COOKIE_SECURE = True # Apenas envia o cookie via HTTPS
    REMEMBER_COOKIE_HTTPONLY = True # Impede acesso via JavaScript
    REMEMBER_COOKIE_SAMESITE = 'Lax' # Proteção CSRF

    # Outras configurações (pode adicionar mais conforme a necessidade)
    DEBUG = True # Mude para False em produção