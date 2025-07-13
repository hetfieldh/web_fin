# app/routes/renda_movimento_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.renda_movimento_model import RendaMovimento
from app.models.renda_model import Renda
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import re

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

renda_movimento_bp = Blueprint('renda_movimento_bp', __name__, template_folder='../templates/renda_movimentos')

@renda_movimento_bp.route('/')
@login_required
def list_renda_movimentos():
    movimentos = RendaMovimento.query.filter_by(usuario_id=current_user.id).order_by(RendaMovimento.mes_ref.desc(), RendaMovimento.mes_pagto.desc()).all()
    return render_template('renda_movimentos/list.html', movimentos=movimentos)

@renda_movimento_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_renda_movimento():
    rendas_disponiveis = Renda.query.filter_by(usuario_id=current_user.id).order_by(Renda.descricao).all()

    if request.method == 'POST':
        renda_id = request.form.get('renda_id')
        mes_ref_str = request.form.get('mes_ref')
        mes_pagto_str = request.form.get('mes_pagto')
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        if not (renda_id and mes_ref_str and mes_pagto_str and valor_str):
            flash('Por favor, preencha todos os campos obrigatórios (Item de Renda, Mês Ref., Mês Pagto., Valor).', 'danger')
            return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)

        try:
            renda_id = int(renda_id)
            renda_obj = Renda.query.filter_by(id=renda_id, usuario_id=current_user.id).first()
            if not renda_obj:
                flash('Item de Renda inválido selecionado.', 'danger')
                return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)
        except ValueError:
            flash('ID de Renda inválido.', 'danger')
            return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)

        try:
            mes_ref = datetime.strptime(mes_ref_str, '%Y-%m').date().replace(day=1)
            mes_pagto = datetime.strptime(mes_pagto_str, '%Y-%m').date().replace(day=1)
        except ValueError:
            flash('Mês de Referência ou Mês de Pagamento inválido. Use o formato YYYY-MM.', 'danger')
            return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)
        
        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)
        except ValueError:
            flash('Valor deve ser um número válido.', 'danger')
            return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)

        new_movimento = RendaMovimento(
            usuario_id=current_user.id,
            renda_id=renda_id,
            mes_ref=mes_ref,
            mes_pagto=mes_pagto,
            valor=valor,
            descricao=descricao
        )
        try:
            db.session.add(new_movimento)
            db.session.commit()
            flash('Movimento de Renda adicionado com sucesso!', 'success')
            return redirect(url_for('renda_movimento_bp.list_renda_movimentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um movimento de renda com esses dados (Item de Renda, Mês Ref., Mês Pagto.) para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar movimento de renda: {e}', 'danger')

    return render_template('renda_movimentos/add.html', rendas_disponiveis=rendas_disponiveis)

@renda_movimento_bp.route('/edit/<int:movimento_id>', methods=['GET', 'POST']) 
@login_required
def edit_renda_movimento(movimento_id): 
    movimento = RendaMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()
    
    rendas_disponiveis = Renda.query.filter_by(usuario_id=current_user.id).order_by(Renda.descricao).all()

    if request.method == 'POST':
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('renda_movimentos/edit.html', 
                                       movimento=movimento,
                                       rendas_disponiveis=rendas_disponiveis)
        except ValueError:
            flash('Valor inválido.', 'danger')
            return render_template('renda_movimentos/edit.html', 
                                   movimento=movimento,
                                   rendas_disponiveis=rendas_disponiveis)
        
        movimento.valor = valor

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('renda_movimentos/edit.html', 
                                   movimento=movimento,
                                   rendas_disponiveis=rendas_disponiveis)
        
        movimento.descricao = descricao

        try:
            db.session.commit()
            flash('Movimento de Renda atualizado com sucesso!', 'success')
            return redirect(url_for('renda_movimento_bp.list_renda_movimentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar movimento. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro inesperado ao atualizar movimento: {e}', 'danger')

    return render_template('renda_movimentos/edit.html', 
                           movimento=movimento,
                           rendas_disponiveis=rendas_disponiveis)

@renda_movimento_bp.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
def delete_renda_movimento(movimento_id):
    movimento = RendaMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(movimento)
        db.session.commit()
        flash('Movimento de Renda excluído com sucesso!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir o registro. Existem itens relacionados a ele.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao excluir movimento: {e}', 'danger')
    
    return redirect(url_for('renda_movimento_bp.list_renda_movimentos'))