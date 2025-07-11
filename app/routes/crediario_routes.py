# app/routes/crediario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.crediario_model import Crediario, tipo_crediario_enum
from sqlalchemy.exc import IntegrityError
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

crediario_bp = Blueprint('crediario_bp', __name__, template_folder='../templates/crediarios')

@crediario_bp.route('/')
@login_required
def list_crediarios():
    crediarios = Crediario.query.filter_by(usuario_id=current_user.id).order_by(Crediario.crediario).all()
    return render_template('crediarios/list.html', crediarios=crediarios)

@crediario_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_crediario():
    tipos_crediario = tipo_crediario_enum.enums

    if request.method == 'POST':
        crediario_nome = request.form.get('crediario')
        tipo_from_form = request.form.get('tipo')
        final = request.form.get('final')
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        if not (crediario_nome and tipo_from_form):
            flash('Por favor, preencha os campos obrigatórios (Nome do Crediário, Tipo).', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        crediario_nome_standardized = standardize_name(crediario_nome)
        if not crediario_nome_standardized:
            flash('O nome do crediário não pode ser vazio.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        if len(crediario_nome_standardized) < 3:
            flash('O nome do crediário deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', crediario_nome_standardized):
            flash('O nome do crediário deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        crediario_nome = crediario_nome_standardized

        tipo_to_save = None
        if tipo_from_form in tipos_crediario:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de crediário inválido selecionado.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        if final:
            final_stripped = final.strip()
            if not final_stripped:
                flash('O campo "Final" não pode ser apenas espaços em branco.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            if not final_stripped.isdigit():
                flash('O campo "Final" deve conter apenas números.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            if len(final_stripped) != 4:
                flash('O campo "Final" deve conter exatamente 4 números.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            final = final_stripped
        else:
            final = None
        
        try:
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite <= 0:
                flash('Limite deve ser um valor positivo (maior que zero).', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        except ValueError:
            flash('Limite deve ser um número válido.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        new_crediario = Crediario(
            usuario_id=current_user.id,
            crediario=crediario_nome,
            tipo=tipo_to_save,
            final=final,
            limite=limite,
            descricao=descricao
        )
        try:
            db.session.add(new_crediario)
            db.session.commit()
            flash('Crediário adicionado com sucesso!', 'success')
            return redirect(url_for('crediario_bp.list_crediarios'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um crediário com esses dados para este usuário (Nome, Tipo, Final).', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar crediário: {e}', 'danger')

    return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

@crediario_bp.route('/edit/<int:crediario_id>', methods=['GET', 'POST'])
@login_required
def edit_crediario(crediario_id):
    crediario = Crediario.query.filter_by(id=crediario_id, usuario_id=current_user.id).first_or_404()
    tipos_crediario = tipo_crediario_enum.enums

    if request.method == 'POST':
        final = request.form.get('final')
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        if final:
            final_stripped = final.strip()
            if not final_stripped:
                flash('O campo "Final" não pode ser apenas espaços em branco.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            if not final_stripped.isdigit():
                flash('O campo "Final" deve conter apenas números.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            if len(final_stripped) != 4:
                flash('O campo "Final" deve conter exatamente 4 números.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            crediario.final = final_stripped
        else:
            crediario.final = None
        
        try:
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite <= 0:
                flash('Limite deve ser um valor positivo (maior que zero).', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
        except ValueError:
            flash('Limite deve ser um número válido.', 'danger')
            return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
        
        crediario.limite = limite

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)

        crediario.descricao = descricao

        try:
            db.session.commit()
            flash('Crediário atualizado com sucesso!', 'success')
            return redirect(url_for('crediario_bp.list_crediarios'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe outro tipo de crediário com esse nome e tipo para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar crediário: {e}', 'danger')

    return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)

@crediario_bp.route('/delete/<int:crediario_id>', methods=['POST'])
@login_required
def delete_crediario(crediario_id):
    crediario = Crediario.query.filter_by(id=crediario_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(crediario)
        db.session.commit()
        flash('Crediário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir crediário: {e}', 'danger')
    
    return redirect(url_for('crediario_bp.list_crediarios'))
