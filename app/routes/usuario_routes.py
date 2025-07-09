# app/routes/usuario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.usuario_model import Usuario, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import re
from sqlalchemy.exc import IntegrityError # Importa IntegrityError

usuario_bp = Blueprint('usuario_bp', __name__, template_folder='../templates/usuarios')

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.default_homepage))

    if request.method == 'POST':
        login_id = request.form.get('login_id')
        senha = request.form.get('senha')

        user = Usuario.query.filter((Usuario.login == login_id) | (Usuario.email == login_id)).first()

        if user and check_password_hash(user.senha_hash, senha):
            if user.is_active:
                login_user(user, remember=True)
                flash('Login bem-sucedido!', 'success')
                next_page = request.args.get('next')
                
                if next_page and next_page != '/':
                    return redirect(next_page)
                else:
                    return redirect(url_for(user.default_homepage))
            else:
                flash('Sua conta está inativa. Por favor, entre em contato com o administrador.', 'danger')
        else:
            flash('Login ou senha inválidos.', 'danger')
    return render_template('login.html')

@usuario_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('usuario_bp.login'))

@usuario_bp.route('/')
@login_required
def list_users():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for(current_user.default_homepage))

    users = Usuario.query.all()
    return render_template('list.html', users=users)

@usuario_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Você não tem permissão para adicionar usuários.', 'danger')
        return redirect(url_for(current_user.default_homepage))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        login = request.form.get('login')
        senha = request.form.get('senha')
        is_active = request.form.get('is_active') == 'on'
        is_admin = request.form.get('is_admin') == 'on'

        if not (nome and email and login and senha):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('add.html')

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Por favor, insira um endereço de e-mail válido.', 'danger')
            return render_template('add.html')

        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return render_template('add.html')

        if Usuario.query.filter_by(login=login).first():
            flash('Este login já está em uso.', 'danger')
            return render_template('add.html')

        senha_hash = generate_password_hash(senha)
        new_user = Usuario(
            nome=nome,
            email=email,
            login=login,
            senha_hash=senha_hash,
            is_active=is_active,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário adicionado com sucesso!', 'success')
        return redirect(url_for('usuario_bp.list_users'))

    return render_template('add.html')

@usuario_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Você não tem permissão para editar usuários.', 'danger')
        return redirect(url_for(current_user.default_homepage))

    user = Usuario.query.get_or_404(user_id)

    if request.method == 'POST':
        user.nome = request.form.get('nome')
        user.email = request.form.get('email')
        user.login = request.form.get('login')
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, user.email):
            flash('Por favor, insira um endereço de e-mail válido.', 'danger')
            return render_template('edit.html', user=user)

        nova_senha = request.form.get('senha')
        if nova_senha:
            user.senha_hash = generate_password_hash(nova_senha)

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('usuario_bp.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {e}', 'danger')

    return render_template('edit.html', user=user)


@usuario_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Você não tem permissão para excluir usuários.', 'danger')
        return redirect(url_for(current_user.default_homepage))

    user = Usuario.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta enquanto estiver logado.', 'danger')
        return redirect(url_for('usuario_bp.list_users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except IntegrityError: # Captura o erro de integridade
        db.session.rollback() # Reverte a transação
        flash('Não foi possível excluir o usuário. Existem contas ou tipos de transação associados a ele. Por favor, exclua-os primeiro.', 'danger')
    except Exception as e: # Captura outros erros inesperados
        db.session.rollback()
        flash(f'Erro inesperado ao excluir usuário: {e}', 'danger')
    
    return redirect(url_for('usuario_bp.list_users'))

