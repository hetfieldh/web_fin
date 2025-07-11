# app/routes/despesa_receita_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.despesa_receita_model import DespesaReceita, tipo_despesa_receita_enum
from sqlalchemy.exc import IntegrityError
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

despesa_receita_bp = Blueprint('despesa_receita_bp', __name__, template_folder='../templates/despesas_receitas')

@despesa_receita_bp.route('/')
@login_required
def list_despesas_receitas():
    items = DespesaReceita.query.filter_by(usuario_id=current_user.id).order_by(DespesaReceita.despesa_receita).all()
    return render_template('despesas_receitas/list.html', items=items)

@despesa_receita_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_despesa_receita():
    tipos_item = tipo_despesa_receita_enum.enums

    if request.method == 'POST':
        despesa_receita_nome = request.form.get('despesa_receita')
        tipo_from_form = request.form.get('tipo')
        descricao = request.form.get('descricao')

        # --- Validações ---
        if not (despesa_receita_nome and tipo_from_form):
            flash('Por favor, preencha os campos obrigatórios (Nome, Tipo).', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)

        despesa_receita_standardized = standardize_name(despesa_receita_nome)
        if not despesa_receita_standardized:
            flash('O nome da despesa/receita não pode ser vazio.', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)
        if len(despesa_receita_standardized) < 3:
            flash('O nome da despesa/receita deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', despesa_receita_standardized):
            flash('O nome da despesa/receita deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)
        despesa_receita_nome = despesa_receita_standardized

        tipo_to_save = None
        if tipo_from_form in tipos_item:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo inválido selecionado.', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('despesas_receitas/add.html', tipos_item=tipos_item)

        new_item = DespesaReceita(
            usuario_id=current_user.id,
            despesa_receita=despesa_receita_nome,
            tipo=tipo_to_save,
            descricao=descricao
        )
        try:
            db.session.add(new_item)
            db.session.commit()
            flash('Despesa/Receita adicionada com sucesso!', 'success')
            return redirect(url_for('despesa_receita_bp.list_despesas_receitas'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe uma despesa/receita com esse nome e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar despesa/receita: {e}', 'danger')

    return render_template('despesas_receitas/add.html', tipos_item=tipos_item)

@despesa_receita_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_despesa_receita(item_id):
    item = DespesaReceita.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()
    tipos_item = tipo_despesa_receita_enum.enums

    if request.method == 'POST':
        descricao = request.form.get('descricao')

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('despesas_receitas/edit.html', item=item, tipos_item=tipos_item)

        item.descricao = descricao

        try:
            db.session.commit()
            flash('Despesa/Receita atualizada com sucesso!', 'success')
            return redirect(url_for('despesa_receita_bp.list_despesas_receitas'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar despesa/receita. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar despesa/receita: {e}', 'danger')

    return render_template('despesas_receitas/edit.html', item=item, tipos_item=tipos_item)

@despesa_receita_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_despesa_receita(item_id):
    item = DespesaReceita.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(item)
        db.session.commit()
        flash('Despesa/Receita excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir despesa/receita: {e}', 'danger')
    
    return redirect(url_for('despesa_receita_bp.list_despesas_receitas'))

