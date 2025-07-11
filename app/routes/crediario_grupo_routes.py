# app/routes/crediario_grupo_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.crediario_grupo_model import CrediarioGrupo, tipo_grupo_crediario_enum
from sqlalchemy.exc import IntegrityError
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

crediario_grupo_bp = Blueprint('crediario_grupo_bp', __name__, template_folder='../templates/crediario_grupos')

@crediario_grupo_bp.route('/')
@login_required
def list_crediario_grupos():
    grupos = CrediarioGrupo.query.filter_by(usuario_id=current_user.id).order_by(CrediarioGrupo.grupo).all()
    return render_template('crediario_grupos/list.html', grupos=grupos)

@crediario_grupo_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_crediario_grupo():
    tipos_grupo = tipo_grupo_crediario_enum.enums

    if request.method == 'POST':
        grupo_nome = request.form.get('grupo')
        tipo_from_form = request.form.get('tipo')
        descricao = request.form.get('descricao')

        if not (grupo_nome and tipo_from_form):
            flash('Por favor, preencha os campos obrigatórios (Nome do Grupo, Tipo).', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)

        grupo_nome_standardized = standardize_name(grupo_nome)
        if not grupo_nome_standardized:
            flash('O nome do grupo não pode ser vazio.', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)
        if len(grupo_nome_standardized) < 3:
            flash('O nome do grupo deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', grupo_nome_standardized):
            flash('O nome do grupo deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)
        grupo_nome = grupo_nome_standardized

        tipo_to_save = None
        if tipo_from_form in tipos_grupo:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de grupo inválido selecionado.', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)

        new_grupo = CrediarioGrupo(
            usuario_id=current_user.id,
            grupo=grupo_nome,
            tipo=tipo_to_save,
            descricao=descricao
        )
        try:
            db.session.add(new_grupo)
            db.session.commit()
            flash('Grupo de Crediário adicionado com sucesso!', 'success')
            return redirect(url_for('crediario_grupo_bp.list_crediario_grupos'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um grupo de crediário com esse nome e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar grupo de crediário: {e}', 'danger')

    return render_template('crediario_grupos/add.html', tipos_grupo=tipos_grupo)

@crediario_grupo_bp.route('/edit/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
def edit_crediario_grupo(grupo_id):
    grupo = CrediarioGrupo.query.filter_by(id=grupo_id, usuario_id=current_user.id).first_or_404()
    tipos_grupo = tipo_grupo_crediario_enum.enums

    if request.method == 'POST':
        descricao = request.form.get('descricao')

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediario_grupos/edit.html', grupo=grupo, tipos_grupo=tipos_grupo)

        grupo.descricao = descricao

        try:
            db.session.commit()
            flash('Grupo de Crediário atualizado com sucesso!', 'success')
            return redirect(url_for('crediario_grupo_bp.list_crediario_grupos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar grupo de crediário. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar grupo de crediário: {e}', 'danger')

    return render_template('crediario_grupos/edit.html', grupo=grupo, tipos_grupo=tipos_grupo)

@crediario_grupo_bp.route('/delete/<int:grupo_id>', methods=['POST'])
@login_required
def delete_crediario_grupo(grupo_id):
    grupo = CrediarioGrupo.query.filter_by(id=grupo_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(grupo)
        db.session.commit()
        flash('Grupo de Crediário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir grupo de crediário: {e}', 'danger')
    
    return redirect(url_for('crediario_grupo_bp.list_crediario_grupos'))

