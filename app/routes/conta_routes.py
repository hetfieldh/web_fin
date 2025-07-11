# app/routes/conta_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_model import Conta, tipo_conta_enum
from sqlalchemy.exc import IntegrityError
import re

conta_bp = Blueprint('conta_bp', __name__, template_folder='../templates/contas')

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

@conta_bp.route('/')
@login_required
def list_contas():
    contas = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco).all()
    return render_template('contas/list.html', contas=contas)

@conta_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_conta():
    tipos_conta = tipo_conta_enum.enums

    if request.method == 'POST':
        nome_banco = request.form.get('nome_banco')
        agencia = request.form.get('agencia')
        conta_num = request.form.get('conta')
        tipo_from_form = request.form.get('tipo')
        saldo_inicial_str = request.form.get('saldo_inicial')
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        if not (nome_banco and conta_num and tipo_from_form):
            flash('Por favor, preencha todos os campos obrigatórios (Banco, Número da Conta, Tipo).', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        nome_banco_standardized = standardize_name(nome_banco)
        if not nome_banco_standardized:
            flash('O nome do banco não pode ser vazio.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)
        if len(nome_banco_standardized) < 3:
            flash('O nome do banco deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)
        nome_banco = nome_banco_standardized

        if agencia:
            if not agencia.isdigit() or len(agencia) != 4:
                flash('Agência deve conter exatamente 4 números.', 'danger')
                return render_template('contas/add.html', tipos_conta=tipos_conta)
            agencia = agencia.zfill(4)

        if not conta_num.isdigit():
            flash('Número da Conta deve conter apenas números.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)
        if len(conta_num) < 6 or len(conta_num) > 20:
            flash('Número da Conta deve ter entre 6 e 20 dígitos.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        tipo_to_save = None
        if tipo_from_form in tipos_conta:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de conta inválido selecionado.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        try:
            saldo_inicial = float(saldo_inicial_str.replace(',', '.')) if saldo_inicial_str else 0.00
            if saldo_inicial < 0:
                flash('Saldo Inicial não pode ser negativo.', 'danger')
                return render_template('contas/add.html', tipos_conta=tipos_conta)

            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite < 0:
                flash('Limite não pode ser negativo.', 'danger')
                return render_template('contas/add.html', tipos_conta=tipos_conta)

        except ValueError:
            flash('Saldo Inicial e Limite devem ser números válidos.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)
        
        if tipo_to_save in ['Corrente', 'Digital']:
            pass
        else:
            if limite > 0:
                flash('Limite só é aplicável para contas do tipo Corrente ou Digital. O limite foi definido como 0.', 'warning')
            limite = 0.00

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('contas/add.html', tipos_conta=tipos_conta)

        new_conta = Conta(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo_to_save,
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

@conta_bp.route('/edit/<int:conta_id>', methods=['GET', 'POST'])
@login_required
def edit_conta(conta_id):
    conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first_or_404()
    tipos_conta = tipo_conta_enum.enums

    if request.method == 'POST':
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        try:
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite < 0:
                flash('Limite não pode ser negativo.', 'danger')
                return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)
        except ValueError:
            flash('Limite deve ser um número válido.', 'danger')
            return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

        if conta.tipo in ['Corrente', 'Digital']:
            conta.limite = limite
        else:
            if limite > 0:
                flash('Limite só é aplicável para contas do tipo Corrente ou Digital. O limite foi definido como 0.', 'warning')
            conta.limite = 0.00

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

        conta.descricao = descricao

        try:
            db.session.commit()
            flash('Conta atualizada com sucesso!', 'success')
            return redirect(url_for('conta_bp.list_contas'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar conta. Verifique os dados.', 'danger') 
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar conta: {e}', 'danger')

    return render_template('contas/edit.html', conta=conta, tipos_conta=tipos_conta)

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
