# app/routes/configuracoes_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.usuario_model import Usuario # Importa o modelo de usuário
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

# Criação do Blueprint para as rotas de configurações
configuracoes_bp = Blueprint('configuracoes_bp', __name__, template_folder='../templates/configuracoes')

# --- Rota para a Página de Configurações de Perfil ---
@configuracoes_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    # Redireciona administradores para o dashboard, pois eles gerenciam usuários em outro local
    if current_user.is_admin:
        flash('Administradores gerenciam usuários na seção "Usuários".', 'info')
        return redirect(url_for('usuario_bp.dashboard'))

    return render_template('configuracoes/settings.html', user=current_user)

# --- Rota para Atualizar Nome e Email do Perfil ---
@configuracoes_bp.route('/settings/update_profile', methods=['POST'])
@login_required
def update_profile():
    if current_user.is_admin:
        flash('Administradores não podem alterar seus próprios dados de perfil por esta rota.', 'danger')
        return redirect(url_for('usuario_bp.dashboard'))

    new_nome = request.form.get('nome')
    new_email = request.form.get('email')

    if not (new_nome and new_email):
        flash('Nome e Email são obrigatórios.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    # Verifica se o email já existe para outro usuário
    existing_user_with_email = Usuario.query.filter(
        Usuario.email == new_email,
        Usuario.id != current_user.id
    ).first()

    if existing_user_with_email:
        flash('Este email já está em uso por outro usuário.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    try:
        current_user.nome = new_nome
        current_user.email = new_email
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {e}', 'danger')

    return redirect(url_for('configuracoes_bp.settings'))

# --- Rota para Alterar Senha ---
@configuracoes_bp.route('/settings/change_password', methods=['POST'])
@login_required
def change_password():
    if current_user.is_admin:
        flash('Administradores não podem alterar suas senhas por esta rota.', 'danger')
        return redirect(url_for('usuario_bp.dashboard'))

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

    if len(new_password) < 6: # Exemplo de validação de senha
        flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
        return redirect(url_for('configuracoes_bp.settings'))

    try:
        current_user.senha_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar senha: {e}', 'danger')

    return redirect(url_for('configuracoes_bp.settings'))

