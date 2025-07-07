# app/routes/conta_transacao_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_transacao_model import ContaTransacao, natureza_transacao_enum
from sqlalchemy.exc import IntegrityError

# Criação do Blueprint para as rotas de tipos de transação
conta_transacao_bp = Blueprint('conta_transacao_bp', __name__, template_folder='../templates/tipos_transacao')

# --- Rota para Listar Tipos de Transação ---
@conta_transacao_bp.route('/')
@login_required
def list_tipos_transacao():
    # Apenas listar os tipos de transação do usuário logado
    tipos_transacao = ContaTransacao.query.filter_by(usuario_id=current_user.id).order_by(ContaTransacao.transacao).all()
    # Explicitamente especifica o caminho completo do template
    return render_template('tipos_transacao/list.html', tipos_transacao=tipos_transacao)

# --- Rota para Adicionar Novo Tipo de Transação ---
@conta_transacao_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_tipo_transacao():
    # Obtém os valores possíveis para o ENUM 'tipo' (Crédito/Débito)
    tipos_natureza = natureza_transacao_enum.enums

    if request.method == 'POST':
        transacao_nome = request.form.get('transacao')
        tipo_natureza = request.form.get('tipo')
        descricao = request.form.get('descricao')

        # Validação básica
        if not (transacao_nome and tipo_natureza):
            flash('Por favor, preencha todos os campos obrigatórios (Nome da Transação, Tipo).', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)
        
        # Validação do tipo de natureza para garantir que está no ENUM
        if tipo_natureza not in tipos_natureza:
            flash('Tipo de natureza de transação inválido selecionado.', 'danger')
            return render_template('tipos_transacao/add.html', tipos_natureza=tipos_natureza)

        new_tipo_transacao = ContaTransacao(
            usuario_id=current_user.id,
            transacao=transacao_nome,
            tipo=tipo_natureza,
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

# --- Rota para Editar Tipo de Transação ---
@conta_transacao_bp.route('/edit/<int:transacao_id>', methods=['GET', 'POST'])
@login_required
def edit_tipo_transacao(transacao_id):
    tipo_transacao = ContaTransacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first_or_404()
    tipos_natureza = natureza_transacao_enum.enums

    if request.method == 'POST':
        tipo_transacao.transacao = request.form.get('transacao')
        tipo_transacao.tipo = request.form.get('tipo')
        tipo_transacao.descricao = request.form.get('descricao')

        if tipo_transacao.tipo not in tipos_natureza:
            flash('Tipo de natureza de transação inválido selecionado.', 'danger')
            return render_template('tipos_transacao/edit.html', tipo_transacao=tipo_transacao, tipos_natureza=tipos_natureza)

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

# --- Rota para Excluir Tipo de Transação ---
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

