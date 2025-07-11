# app/routes/despesa_fixa_routes.py
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.despesa_fixa_model import DespesaFixa
from app.models.despesa_receita_model import DespesaReceita # Para selecionar o item de despesa/receita
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

despesa_fixa_bp = Blueprint('despesa_fixa_bp', __name__, template_folder='../templates/despesas_fixas')

@despesa_fixa_bp.route('/')
@login_required
def list_despesas_fixas():
    despesas_fixas = DespesaFixa.query.filter_by(usuario_id=current_user.id).order_by(DespesaFixa.mes_ano.desc()).all()
    return render_template('despesas_fixas/list.html', despesas_fixas=despesas_fixas)

@despesa_fixa_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_despesa_fixa():
    despesas_receitas_disponiveis = DespesaReceita.query.filter_by(
        usuario_id=current_user.id, tipo='Despesa'
    ).order_by(DespesaReceita.despesa_receita).all()

    if request.method == 'POST':
        despesa_receita_id = request.form.get('despesa_receita_id')
        mes_ano_str = request.form.get('mes_ano')
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        if not (despesa_receita_id and mes_ano_str and valor_str):
            flash('Por favor, preencha todos os campos obrigatórios (Item, Mês/Ano, Valor).', 'danger')
            return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)

        try:
            despesa_receita_id = int(despesa_receita_id)
            item_despesa_receita = DespesaReceita.query.filter_by(
                id=despesa_receita_id, usuario_id=current_user.id, tipo='Despesa'
            ).first()
            if not item_despesa_receita:
                flash('Item de Despesa/Receita inválido selecionado.', 'danger')
                return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        except ValueError:
            flash('Item de Despesa/Receita inválido.', 'danger')
            return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)

        try:
            mes_ano = datetime.strptime(mes_ano_str, '%Y-%m').date()
        except ValueError:
            flash('Mês/Ano inválido. Use o formato YYYY-MM.', 'danger')
            return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        except ValueError:
            flash('Valor deve ser um número válido.', 'danger')
            return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)

        new_despesa_fixa = DespesaFixa(
            usuario_id=current_user.id,
            despesa_receita_id=despesa_receita_id,
            mes_ano=mes_ano,
            valor=valor,
            descricao=descricao
        )
        try:
            db.session.add(new_despesa_fixa)
            db.session.commit()
            flash('Despesa Fixa adicionada com sucesso!', 'success')
            return redirect(url_for('despesa_fixa_bp.list_despesas_fixas'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe uma despesa fixa para este item e mês/ano.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar despesa fixa: {e}', 'danger')

    return render_template('despesas_fixas/add.html', despesas_receitas_disponiveis=despesas_receitas_disponiveis)

@despesa_fixa_bp.route('/edit/<int:despesa_fixa_id>', methods=['GET', 'POST'])
@login_required
def edit_despesa_fixa(despesa_fixa_id):
    despesa_fixa = DespesaFixa.query.filter_by(id=despesa_fixa_id, usuario_id=current_user.id).first_or_404()
    
    despesas_receitas_disponiveis = DespesaReceita.query.filter_by(
        usuario_id=current_user.id, tipo='Despesa'
    ).order_by(DespesaReceita.despesa_receita).all()

    if request.method == 'POST':
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('despesas_fixas/edit.html', despesa_fixa=despesa_fixa, despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        except ValueError:
            flash('Valor deve ser um número válido.', 'danger')
            return render_template('despesas_fixas/edit.html', despesa_fixa=despesa_fixa, despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        
        despesa_fixa.valor = valor

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('despesas_fixas/edit.html', despesa_fixa=despesa_fixa, despesas_receitas_disponiveis=despesas_receitas_disponiveis)
        
        despesa_fixa.descricao = descricao

        try:
            db.session.commit()
            flash('Despesa Fixa atualizada com sucesso!', 'success')
            return redirect(url_for('despesa_fixa_bp.list_despesas_fixas'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar despesa fixa. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar despesa fixa: {e}', 'danger')

    return render_template('despesas_fixas/edit.html', despesa_fixa=despesa_fixa, despesas_receitas_disponiveis=despesas_receitas_disponiveis)

@despesa_fixa_bp.route('/delete/<int:despesa_fixa_id>', methods=['POST'])
@login_required
def delete_despesa_fixa(despesa_fixa_id):
    despesa_fixa = DespesaFixa.query.filter_by(id=despesa_fixa_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(despesa_fixa)
        db.session.commit()
        flash('Despesa Fixa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir despesa fixa: {e}', 'danger')
    
    return redirect(url_for('despesa_fixa_bp.list_despesas_fixas'))
