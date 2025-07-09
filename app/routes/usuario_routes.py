# app/routes/usuario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.usuario_model import Usuario, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import re # Importa o módulo de expressões regulares

usuario_bp = Blueprint('usuario_bp', __name__, template_folder='../templates/usuarios')

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Se já autenticado, redireciona para a página inicial padrão do usuário
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
                
                # NOVO: Lógica de redirecionamento mais explícita
                # Se houver um 'next_page' e ele não for a raiz ('/'), redirecione para ele.
                # Caso contrário, use a default_homepage do usuário.
                if next_page and next_page != '/': # ALTERADO: Comparando com a string '/' diretamente
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

# Rota para Listar Usuários (agora é a raiz do Blueprint de usuário: /usuarios/)
@usuario_bp.route('/') # ALTERADO: Rota agora é a raiz do Blueprint de usuário
@login_required
def list_users():
    if not current_user.is_admin:
        flash('Você não tem permissão para acessar esta página.', 'danger')
        # Redireciona para a página inicial padrão do usuário
        return redirect(url_for(current_user.default_homepage))

    users = Usuario.query.all()
    return render_template('list.html', users=users)

@usuario_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Você não tem permissão para adicionar usuários.', 'danger')
        # Redireciona para o NOVO dashboard_bp.dashboard
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

        # Validação de formato de e-mail
        # Regex para validar o formato básico de e-mail
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
        # Redireciona para o NOVO dashboard_bp.dashboard
        return redirect(url_for(current_user.default_homepage))

    user = Usuario.query.get_or_404(user_id)

    if request.method == 'POST':
        user.nome = request.form.get('nome')
        user.email = request.form.get('email')
        user.login = request.form.get('login')
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'

        # Validação de formato de e-mail para edição também
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, user.email): # Valida o email que foi atribuído
            flash('Por favor, insira um endereço de e-mail válido.', 'danger')
            return render_template('edit.html', user=user) # Retorna o template com os dados atuais

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
        # Redireciona para o NOVO dashboard_bp.dashboard
        return redirect(url_for(current_user.default_homepage))

    user = Usuario.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta enquanto estiver logado.', 'danger')
        return redirect(url_for('usuario_bp.list_users'))

    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuario_bp.list_users'))
