# app/routes/usuario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from psycopg2 import IntegrityError
from app.models.usuario_model import Usuario, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import re

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
        confirm_senha = request.form.get('confirm_senha')
        is_active = request.form.get('is_active') == 'on'
        is_admin = request.form.get('is_admin') == 'on'

        if not (nome and email and login and senha and confirm_senha):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('add.html')

        # Validação do campo Nome
        nome_stripped = nome.strip()
        if not nome_stripped:
            flash('O nome não pode ser vazio.', 'danger')
            return render_template('add.html')
        
        # Divide o nome em partes e filtra partes vazias (para múltiplos espaços)
        nome_partes = [parte for parte in nome_stripped.split() if parte]
        
        if len(nome_partes) < 2: # Pelo menos dois nomes (nome e sobrenome)
            flash('Por favor, digite pelo menos o nome e o sobrenome.', 'danger')
            return render_template('add.html')
        
        # NOVO: Validação para que cada parte do nome tenha mais de 1 caractere
        for parte in nome_partes:
            if len(parte) <= 1:
                flash('Cada parte do nome (nome e sobrenome) deve ter mais de um caractere.', 'danger')
                return render_template('add.html')

        if not re.fullmatch(r'^[a-zA-Z\sÀ-ÿ]+$', nome_stripped): # Sem números ou caracteres especiais
            flash('O nome não pode conter números ou caracteres especiais.', 'danger')
            return render_template('add.html')

        # Validação de formato de e-mail e conversão para minúsculas
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Por favor, insira um endereço de e-mail válido.', 'danger')
            return render_template('add.html')
        email = email.lower()

        # Validação de força da senha e confirmação
        if senha != confirm_senha:
            flash('A senha e a confirmação de senha não coincidem.', 'danger')
            return render_template('add.html')
        if len(senha) < 8:
            flash('A senha deve ter no mínimo 8 caracteres.', 'danger')
            return render_template('add.html')
        if not re.search(r'\d', senha):
            flash('A senha deve conter pelo menos um número.', 'danger')
            return render_template('add.html')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            flash('A senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?":{}|<>).', 'danger')
            return render_template('add.html')
        
        common_passwords = ['12345678', 'password', 'qwerty', 'admin', 'usuario', 'senha123']
        if senha.lower() in common_passwords:
            flash('Esta senha é muito comum. Por favor, escolha uma senha mais forte.', 'danger')
            return render_template('add.html')


        # Validação do campo Login
        login_stripped = login.strip()
        if not login_stripped:
            flash('O login não pode ser vazio.', 'danger')
            return render_template('add.html')
        login_regex = r'^[a-z][a-zA-Z0-9_.-]{3,}$'
        if len(login_stripped) < 4:
            flash('O login deve ter no mínimo 4 caracteres.', 'danger')
            return render_template('add.html')
        if not re.match(login_regex, login_stripped):
            flash('O login deve começar com uma letra minúscula e conter apenas letras, números, sublinhados, hífens ou pontos.', 'danger')
            return render_template('add.html')
        
        login = login_stripped 


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
        nova_senha = request.form.get('senha')
        confirm_nova_senha = request.form.get('confirm_senha')
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'

        # Validação do campo Nome para edição
        nome_stripped = user.nome.strip()
        if not nome_stripped:
            flash('O nome não pode ser vazio.', 'danger')
            return render_template('edit.html', user=user)
        
        nome_partes = [parte for parte in nome_stripped.split() if parte]
        if len(nome_partes) < 2:
            flash('Por favor, digite pelo menos o nome e o sobrenome.', 'danger')
            return render_template('edit.html', user=user)
        
        for parte in nome_partes:
            if len(parte) <= 1:
                flash('Cada parte do nome (nome e sobrenome) deve ter mais de um caractere.', 'danger')
                return render_template('edit.html', user=user)

        if not re.fullmatch(r'^[a-zA-Z\sÀ-ÿ]+$', nome_stripped):
            flash('O nome não pode conter números ou caracteres especiais.', 'danger')
            return render_template('edit.html', user=user)
        user.nome = nome_stripped


        # Validação de formato de e-mail e conversão para minúsculas para edição
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, user.email):
            flash('Por favor, insira um endereço de e-mail válido.', 'danger')
            return render_template('edit.html', user=user)
        user.email = user.email.lower()

        # Validação do campo Login para edição
        login_stripped = user.login.strip()
        if not login_stripped:
            flash('O login não pode ser vazio.', 'danger')
            return render_template('edit.html', user=user)
        login_regex = r'^[a-z][a-zA-Z0-9_.-]{3,}$'
        if len(login_stripped) < 4:
            flash('O login deve ter no mínimo 4 caracteres.', 'danger')
            return render_template('edit.html', user=user)
        original_user = Usuario.query.get(user_id)
        if login_stripped != original_user.login and Usuario.query.filter_by(login=login_stripped).first():
            flash('Este login já está em uso.', 'danger')
            return render_template('edit.html', user=user)
        if not re.match(login_regex, login_stripped):
            flash('O login deve começar com uma letra minúscula e conter apenas letras, números, sublinhados, hífens ou pontos.', 'danger')
            return render_template('edit.html', user=user)
        user.login = login_stripped


        if nova_senha:
            if nova_senha != confirm_nova_senha:
                flash('A nova senha e a confirmação de senha não coincidem.', 'danger')
                return render_template('edit.html', user=user)
            if len(nova_senha) < 8:
                flash('A nova senha deve ter no mínimo 8 caracteres.', 'danger')
                return render_template('edit.html', user=user)
            if not re.search(r'\d', nova_senha):
                flash('A nova senha deve conter pelo menos um número.', 'danger')
                return render_template('edit.html', user=user)
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', nova_senha):
                flash('A nova senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?":{}|<>).', 'danger')
                return render_template('edit.html', user=user)
            
            common_passwords = ['12345678', 'password', 'qwerty', 'admin', 'usuario', 'senha123']
            if nova_senha.lower() in common_passwords:
                flash('Esta senha é muito comum. Por favor, escolha uma senha mais forte.', 'danger')
                return render_template('edit.html', user=user)

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
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir o usuário. Existem contas ou tipos de transação associados a ele. Por favor, exclua-os primeiro.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao excluir usuário: {e}', 'danger')
    
    return redirect(url_for('usuario_bp.list_users'))
