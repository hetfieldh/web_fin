# app/routes/configuracoes_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, login_user
from app import db, login_manager
from app.models.usuario_model import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import re

configuracoes_bp = Blueprint('configuracoes_bp', __name__, template_folder='../templates/configuracoes')

@configuracoes_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    if current_user.is_admin:
        flash('Administradores gerenciam usuários na seção "Usuários".', 'info')
        return redirect(url_for('dashboard_bp.dashboard'))

    homepage_options = [
        ('dashboard_bp.dashboard', 'Dashboard'),
        ('conta_bp.list_contas', 'Minhas Contas'),
        ('crediario_bp.list_crediarios', 'Crediários'), 
        ('renda_bp.list_rendas', 'Rendas'), 
        ('despesa_receita_bp.list_despesas_receitas', 'Despesas e Receitas'),
        ('extrato_bancario_bp.selecionar_extrato', 'Extrato Bancário'),
        ('extrato_crediario_bp.selecionar_extrato_crediario', 'Extrato Crediário'),
        ('financiamento_bp.list_financiamentos', 'Financiamentos')
    ]

    return render_template('configuracoes/settings.html', user=current_user, homepage_options=homepage_options)

@configuracoes_bp.route('/settings/update_profile', methods=['POST'])
@login_required
def update_profile():
    if current_user.is_admin:
        flash('Administradores não podem alterar seus próprios dados de perfil por esta rota.', 'danger')
        return redirect(url_for('dashboard_bp.dashboard'))

    new_nome = request.form.get('nome')
    new_email = request.form.get('email')

    if not (new_nome and new_email):
        flash('Nome e Email são obrigatórios.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    nome_stripped = new_nome.strip()
    if not nome_stripped:
        flash('O nome não pode ser vazio.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    
    nome_partes = [parte for parte in nome_stripped.split() if parte]
    if len(nome_partes) < 2:
        flash('Por favor, digite pelo menos o nome e o sobrenome.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    
    for parte in nome_partes:
        if len(parte) <= 1:
            flash('Cada parte do nome (nome e sobrenome) deve ter mais de um caractere.', 'danger')
            return redirect(url_for('configuracoes_bp.settings'))

    if not re.fullmatch(r'^[a-zA-Z\sÀ-ÿ]+$', nome_stripped):
        flash('O nome não pode conter números ou caracteres especiais.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))


    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, new_email):
        flash('Por favor, insira um endereço de e-mail válido.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    new_email = new_email.lower()

    existing_user_with_email = Usuario.query.filter(
        Usuario.email == new_email,
        Usuario.id != current_user.id
    ).first()

    if existing_user_with_email:
        flash('Este email já está em uso por outro usuário.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    try:
        current_user.nome = nome_stripped
        current_user.email = new_email
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        login_user(current_user, remember=True)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {e}', 'danger')

    return redirect(url_for('configuracoes_bp.settings'))

@configuracoes_bp.route('/settings/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.is_admin:
        flash('Administradores não podem alterar suas senhas por esta rota.', 'danger')
        return redirect(url_for('dashboard_bp.dashboard'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not (current_password and new_password and confirm_password):
        flash('Por favor, preencha todos os campos de senha.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    if not check_password_hash(current_user.senha_hash, current_password):
        flash('Senha atual incorreta.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    if new_password != confirm_password:
        flash('A nova senha e a confirmação de senha não coincidem.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    if len(new_password) < 8:
        flash('A nova senha deve ter no mínimo 8 caracteres.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    if not re.search(r'\d', new_password):
        flash('A nova senha deve conter pelo menos um número.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
        flash('A nova senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?":{}|<>).', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))
    
    common_passwords = ['12345678', 'password', 'qwerty', 'admin', 'usuario', 'senha123']
    if new_password.lower() in common_passwords:
        flash('Esta senha é muito comum. Por favor, escolha uma senha mais forte.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    try:
        current_user.senha_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
        login_user(current_user, remember=True)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar senha: {e}', 'danger')

    return redirect(url_for('configuracoes_bp.settings'))

@configuracoes_bp.route('/settings/update_homepage', methods=['POST'])
@login_required
def update_homepage():
    if current_user.is_admin:
        flash('Administradores não podem alterar a página inicial padrão por esta rota.', 'danger')
        return redirect(url_for('dashboard_bp.dashboard'))

    new_homepage = request.form.get('default_homepage')

    valid_homepage_routes = [
        'dashboard_bp.dashboard',
        'conta_bp.list_contas',
        'crediario_bp.list_crediarios', 
        'renda_bp.list_rendas', 
        'despesa_receita_bp.list_despesas_receitas',
        'extrato_bancario_bp.selecionar_extrato',
        'extrato_crediario_bp.selecionar_extrato_crediario',
        'financiamento_bp.list_financiamentos'
    ]
    if new_homepage not in valid_homepage_routes:
        flash('Página inicial padrão inválida selecionada.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    try:
        current_user.default_homepage = new_homepage
        db.session.commit()
        flash('Página inicial padrão atualizada com sucesso!', 'success')
        login_user(current_user, remember=True)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar página inicial padrão: {e}', 'danger')

    return redirect(url_for('configuracoes_bp.settings'))
