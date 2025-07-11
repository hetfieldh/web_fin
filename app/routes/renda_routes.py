# app/routes/renda_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.renda_model import Renda, tipo_renda_enum
from sqlalchemy.exc import IntegrityError
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

renda_bp = Blueprint('renda_bp', __name__, template_folder='../templates/rendas')

@renda_bp.route('/')
@login_required
def list_rendas():
    rendas = Renda.query.filter_by(usuario_id=current_user.id).order_by(Renda.descricao).all()
    return render_template('rendas/list.html', rendas=rendas)

@renda_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_renda():
    tipos_renda = tipo_renda_enum.enums

    if request.method == 'POST':
        descricao_renda = request.form.get('descricao')
        tipo_from_form = request.form.get('tipo')

        if not (descricao_renda and tipo_from_form):
            flash('Por favor, preencha os campos obrigatórios (Descrição, Tipo).', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)

        descricao_renda_standardized = standardize_name(descricao_renda)
        if not descricao_renda_standardized:
            flash('A descrição da renda não pode ser vazia.', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)
        if len(descricao_renda_standardized) < 3:
            flash('A descrição da renda deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', descricao_renda_standardized):
            flash('A descrição da renda deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)
        descricao_renda = descricao_renda_standardized

        tipo_to_save = None
        if tipo_from_form in tipos_renda:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de renda inválido selecionado.', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)
        
        if len(descricao_renda) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('rendas/add.html', tipos_renda=tipos_renda)

        new_renda = Renda(
            usuario_id=current_user.id,
            descricao=descricao_renda,
            tipo=tipo_to_save
        )
        try:
            db.session.add(new_renda)
            db.session.commit()
            flash('Renda adicionada com sucesso!', 'success')
            return redirect(url_for('renda_bp.list_rendas'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe uma renda com essa descrição e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar renda: {e}', 'danger')

    return render_template('rendas/add.html', tipos_renda=tipos_renda)

@renda_bp.route('/edit/<int:renda_id>', methods=['GET', 'POST'])
@login_required
def edit_renda(renda_id):
    renda = Renda.query.filter_by(id=renda_id, usuario_id=current_user.id).first_or_404()
    tipos_renda = tipo_renda_enum.enums

    if request.method == 'POST':
        tipo_from_form = request.form.get('tipo')

        tipo_to_save = None
        if tipo_from_form in tipos_renda:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de renda inválido selecionado.', 'danger')
            return render_template('rendas/edit.html', renda=renda, tipos_renda=tipos_renda)
        
        renda.tipo = tipo_to_save

        try:
            db.session.commit()
            flash('Renda atualizada com sucesso!', 'success')
            return redirect(url_for('renda_bp.list_rendas'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar renda. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar renda: {e}', 'danger')

    return render_template('rendas/edit.html', renda=renda, tipos_renda=tipos_renda)

@renda_bp.route('/delete/<int:renda_id>', methods=['POST'])
@login_required
def delete_renda(renda_id):
    renda = Renda.query.filter_by(id=renda_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(renda)
        db.session.commit()
        flash('Renda excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir renda: {e}', 'danger')
    
    return redirect(url_for('renda_bp.list_rendas'))

