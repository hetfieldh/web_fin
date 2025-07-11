# app/routes/conta_transacao_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_transacao_model import ContaTransacao, tipo_natureza_transacao_enum 
from sqlalchemy.exc import IntegrityError
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

conta_transacao_bp = Blueprint('conta_transacao_bp', __name__, template_folder='../templates/tipos_transacao')

@conta_transacao_bp.route('/')
@login_required
def list_tipos_transacao():
    tipos_transacao = ContaTransacao.query.filter_by(usuario_id=current_user.id).order_by(ContaTransacao.transacao).all()
    return render_template('tipos_transacao/list.html', tipos_transacao=tipos_transacao)

@conta_transacao_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_tipo_transacao():
    tipos_natureza = tipo_natureza_transacao_enum.enums

    if request.method == 'POST':
        transacao_nome = request.form.get('transacao')
        tipo_natureza = request.form.get('tipo')
        descricao = request.form.get('descricao')

        if not (transacao_nome and tipo_natureza):
            flash('Por favor, preencha todos os campos obrigatórios (Nome da Transação, Tipo).', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)

        transacao_nome_standardized = standardize_name(transacao_nome)
        if not transacao_nome_standardized:
            flash('O nome da transação não pode ser vazio.', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)
        if len(transacao_nome_standardized) < 3:
            flash('O nome da transação deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)
        transacao_nome = transacao_nome_standardized

        tipo_to_save = None
        if tipo_natureza in tipos_natureza:
            tipo_to_save = tipo_natureza
        
        if tipo_to_save is None:
            flash('Tipo de natureza de transação inválido selecionado.', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)

        new_tipo_transacao = ContaTransacao(
            usuario_id=current_user.id,
            transacao=transacao_nome,
            tipo=tipo_to_save,
            descricao=descricao
        )
        try:
            db.session.add(new_tipo_transacao)
            db.session.commit()
            flash('Tipo de transação adicionado com sucesso!', 'success')
            return redirect(url_for('conta_transacao_bp.list_tipos_transacao'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um tipo de transação com esse nome e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar tipo de transação: {e}', 'danger')

    return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)

@conta_transacao_bp.route('/edit/<int:transacao_id>', methods=['GET', 'POST'])
@login_required
def edit_tipo_transacao(transacao_id):
    tipo_transacao = ContaTransacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first_or_404()
    tipos_natureza = tipo_natureza_transacao_enum.enums

    if request.method == 'POST':
        tipo_natureza = request.form.get('tipo')
        descricao = request.form.get('descricao')

        tipo_to_save = None
        if tipo_natureza in tipos_natureza:
            tipo_to_save = tipo_natureza
        
        if tipo_to_save is None:
            flash('Tipo de natureza de transação inválido selecionado.', 'danger')
            return render_template('tipos_transacao/edit.html', tipo_transacao=tipo_transacao, tipos_natureza=tipos_natureza)
        
        tipo_transacao.tipo = tipo_to_save

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('tipos_transacao/edit.html', tipo_transacao=tipo_transacao, tipos_natureza=tipos_natureza)

        tipo_transacao.descricao = descricao

        try:
            db.session.commit()
            flash('Tipo de transação atualizado com sucesso!', 'success')
            return redirect(url_for('conta_transacao_bp.list_tipos_transacao'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe outro tipo de transação com esse nome e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tipo de transação: {e}', 'danger')

    return render_template('tipos_transacao/edit.html', tipo_transacao=tipo_transacao, tipos_natureza=tipos_natureza)

@conta_transacao_bp.route('/delete/<int:transacao_id>', methods=['POST'])
@login_required
def delete_tipo_transacao(transacao_id):
    tipo_transacao = ContaTransacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(tipo_transacao)
        db.session.commit()
        flash('Tipo de transação excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tipo de transação: {e}', 'danger')
    
    return redirect(url_for('conta_transacao_bp.list_tipos_transacao'))
