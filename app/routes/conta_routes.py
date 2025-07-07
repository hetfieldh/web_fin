# app/routes/conta_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_model import Conta, tipo_conta_enum
from sqlalchemy.exc import IntegrityError

# Criação do Blueprint para as rotas de contas
conta_bp = Blueprint('conta_bp', __name__, template_folder='../templates/contas')

# --- Rota para Listar Contas ---
@conta_bp.route('/')
@login_required
def list_contas():
    # Apenas listar as contas do usuário logado
    contas = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco).all()
    # Explicitamente especifica o caminho completo do template dentro da pasta templates
    return render_template('contas/list.html', contas=contas)

# --- Rota para Adicionar Nova Conta ---
@conta_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_conta():
    # Obtém os valores possíveis para o ENUM 'tipo' usando .enums
    tipos_conta = tipo_conta_enum.enums # CORRIGIDO: Usando .enums

    if request.method == 'POST':
        nome_banco = request.form.get('nome_banco')
        agencia = request.form.get('agencia')
        conta_num = request.form.get('conta')
        tipo = request.form.get('tipo')
        saldo_inicial_str = request.form.get('saldo_inicial')
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        # Validação básica
        if not (nome_banco and conta_num and tipo):
            flash('Por favor, preencha todos os campos obrigatórios (Banco, Número da Conta, Tipo).', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        try:
            # Converte vírgula para ponto para permitir float()
            saldo_inicial = float(saldo_inicial_str.replace(',', '.')) if saldo_inicial_str else 0.00
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
        except ValueError:
            flash('Saldo inicial e Limite devem ser números válidos.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)
        
        # Validação do tipo de conta para garantir que está no ENUM
        if tipo not in tipos_conta:
            flash('Tipo de conta inválido selecionado.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        new_conta = Conta(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
            limite=limite,
            descricao=descricao
        )
        try:
            db.session.add(new_conta)
            db.session.commit()
            flash('Conta adicionada com sucesso!', 'success')
            return redirect(url_for('conta_bp.list_contas'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe uma conta com esses dados para este usuário (Banco, Agência, Conta, Tipo).', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar conta: {e}', 'danger')

    return render_template('contas/add.html', tipos_conta=tipos_conta)

# --- Rota para Editar Conta ---
@conta_bp.route('/edit/<int:conta_id>', methods=['GET', 'POST'])
@login_required
def edit_conta(conta_id):
    conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first_or_404()
    # Obtém os valores possíveis para o ENUM 'tipo' usando .enums
    tipos_conta = tipo_conta_enum.enums # CORRIGIDO: Usando .enums

    if request.method == 'POST':
        conta.nome_banco = request.form.get('nome_banco')
        conta.agencia = request.form.get('agencia')
        conta.conta = request.form.get('conta')
        conta.tipo = request.form.get('tipo')
        saldo_inicial_str = request.form.get('saldo_inicial')
        limite_str = request.form.get('limite')
        conta.descricao = request.form.get('descricao')

        try:
            saldo_inicial = float(saldo_inicial_str.replace(',', '.')) if saldo_inicial_str else 0.00
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
        except ValueError:
            flash('Saldo inicial e Limite devem ser números válidos.', 'danger')
            return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

        if conta.tipo not in tipos_conta:
            flash('Tipo de conta inválido selecionado.', 'danger')
            return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

        try:
            db.session.commit()
            flash('Conta atualizada com sucesso!', 'success')
            return redirect(url_for('conta_bp.list_contas'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe outra conta com esses dados (Banco, Agência, Conta, Tipo) para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar conta: {e}', 'danger')

    return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

# --- Rota para Excluir Conta ---
@conta_bp.route('/delete/<int:conta_id>', methods=['POST'])
@login_required
def delete_conta(conta_id):
    conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(conta)
        db.session.commit()
        flash('Conta excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir conta: {e}', 'danger')
    
    return redirect(url_for('conta_bp.list_contas'))
