# app/routes/crediario_movimento_routes.py
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_model import Crediario
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_parcela_model import CrediarioParcela
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from dateutil.relativedelta import relativedelta

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

crediario_movimento_bp = Blueprint('crediario_movimento_bp', __name__, template_folder='../templates/crediario_movimentos')

@crediario_movimento_bp.route('/')
@login_required
def list_movimentos_crediario():
    movimentos = CrediarioMovimento.query.filter_by(usuario_id=current_user.id).order_by(CrediarioMovimento.data_compra.desc(), CrediarioMovimento.data_criacao.desc()).all()
    return render_template('crediario_movimentos/list.html', movimentos=movimentos)

@crediario_movimento_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento_crediario():
    crediarios_disponiveis = Crediario.query.filter_by(usuario_id=current_user.id).order_by(Crediario.crediario).all()
    grupos_disponiveis = CrediarioGrupo.query.filter_by(usuario_id=current_user.id).order_by(CrediarioGrupo.grupo).all()

    if request.method == 'POST':
        crediario_id = request.form.get('crediario_id')
        crediario_grupo_id = request.form.get('crediario_grupo_id')
        data_compra_str = request.form.get('data_compra')
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total')
        num_parcelas_str = request.form.get('num_parcelas')
        primeira_parcela_str = request.form.get('primeira_parcela')

        if not (crediario_id and crediario_grupo_id and data_compra_str and valor_total_str and num_parcelas_str and primeira_parcela_str):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('crediario_movimentos/add.html', 
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)

        try:
            crediario_id = int(crediario_id)
            crediario_grupo_id = int(crediario_grupo_id)
            
            crediario_obj = Crediario.query.filter_by(id=crediario_id, usuario_id=current_user.id).first()
            grupo_obj = CrediarioGrupo.query.filter_by(id=crediario_grupo_id, usuario_id=current_user.id).first()

            if not crediario_obj:
                flash('Crediário inválido selecionado.', 'danger')
                return render_template('crediario_movimentos/add.html', 
                                       crediarios_disponiveis=crediarios_disponiveis,
                                       grupos_disponiveis=grupos_disponiveis)
            if not grupo_obj:
                flash('Grupo de Crediário inválido selecionado.', 'danger')
                return render_template('crediario_movimentos/add.html', 
                                       crediarios_disponiveis=crediarios_disponiveis,
                                       grupos_disponiveis=grupos_disponiveis)
        except ValueError:
            flash('IDs de Crediário ou Grupo de Crediário inválidos.', 'danger')
            return render_template('crediario_movimentos/add.html', 
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)

        try:
            data_compra = datetime.strptime(data_compra_str, '%Y-%m-%d').date()
            primeira_parcela = datetime.strptime(primeira_parcela_str, '%Y-%m').date().replace(day=1) 
        except ValueError:
            flash('Data de Compra ou Primeira Parcela inválida. Use o formato YYYY-MM-DD para Data da Compra e YYYY-MM para Primeira Parcela.', 'danger')
            return render_template('crediario_movimentos/add.html', 
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)
        
        try:
            valor_total = float(valor_total_str.replace(',', '.'))
            if valor_total <= 0:
                flash('Valor Total deve ser um número positivo (maior que zero).', 'danger')
                return render_template('crediario_movimentos/add.html', 
                                       crediarios_disponiveis=crediarios_disponiveis,
                                       grupos_disponiveis=grupos_disponiveis)
            
            num_parcelas = int(num_parcelas_str)
            if num_parcelas <= 0:
                flash('Número de Parcelas deve ser um número inteiro positivo (maior que zero).', 'danger')
                return render_template('crediario_movimentos/add.html', 
                                       crediarios_disponiveis=crediarios_disponiveis,
                                       grupos_disponiveis=grupos_disponiveis)
            
            valor_parcela_mensal = round(valor_total / num_parcelas, 2)

            ultima_parcela = primeira_parcela + relativedelta(months=num_parcelas - 1)

        except ValueError:
            flash('Valor Total ou Número de Parcelas inválidos.', 'danger')
            return render_template('crediario_movimentos/add.html', 
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediario_movimentos/add.html', 
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)

        new_movimento = CrediarioMovimento(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            crediario_grupo_id=crediario_grupo_id,
            data_compra=data_compra,
            descricao=descricao,
            valor_total=valor_total,
            num_parcelas=num_parcelas,
            primeira_parcela=primeira_parcela,
            ultima_parcela=ultima_parcela,
            valor_parcela_mensal=valor_parcela_mensal
        )
        try:
            db.session.add(new_movimento)
            db.session.commit()

            if new_movimento.num_parcelas > 0:
                for i in range(new_movimento.num_parcelas):
                    vencimento_parcela = new_movimento.primeira_parcela + relativedelta(months=i)
                    parcela = CrediarioParcela(
                        crediario_movimento_id=new_movimento.id,
                        numero_parcela=i + 1,
                        vencimento=vencimento_parcela,
                        valor_parcela=new_movimento.valor_parcela_mensal
                    )
                    db.session.add(parcela)
                db.session.commit()

            flash('Movimentação de Crediário adicionada com sucesso!', 'success')
            return redirect(url_for('crediario_movimento_bp.list_movimentos_crediario'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe uma movimentação de crediário com esses dados (Crediário, Grupo, Data, Descrição, Valor Total) para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar movimentação: {e}', 'danger')

    return render_template('crediario_movimentos/add.html', 
                           crediarios_disponiveis=crediarios_disponiveis,
                           grupos_disponiveis=grupos_disponiveis)

@crediario_movimento_bp.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
def edit_movimento_crediario(movimento_id):
    movimento = CrediarioMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()
    
    crediarios_disponiveis = Crediario.query.filter_by(usuario_id=current_user.id).order_by(Crediario.crediario).all()
    grupos_disponiveis = CrediarioGrupo.query.filter_by(usuario_id=current_user.id).order_by(CrediarioGrupo.grupo).all()

    if request.method == 'POST':
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor_total')

        try:
            valor_total = float(valor_total_str.replace(',', '.'))
            if valor_total <= 0:
                flash('Valor Total deve ser um número positivo (maior que zero).', 'danger')
                return render_template('crediario_movimentos/edit.html', 
                                       movimento=movimento,
                                       crediarios_disponiveis=crediarios_disponiveis,
                                       grupos_disponiveis=grupos_disponiveis)
        except ValueError:
            flash('Valor Total inválido.', 'danger')
            return render_template('crediario_movimentos/edit.html', 
                                   movimento=movimento,
                                   crediarios_disponiveis=crediarios_disponiveis,
                                   grupos_disponiveis=grupos_disponiveis)
        
        if movimento.valor_total != valor_total:
            movimento.valor_total = valor_total
            movimento.valor_parcela_mensal = round(movimento.valor_total / movimento.num_parcelas, 2)
            for parcela in movimento.parcelas:
                parcela.valor_parcela = movimento.valor_parcela_mensal
        
        movimento.descricao = descricao

        try:
            db.session.commit()
            flash('Movimentação de Crediário atualizada com sucesso!', 'success')
            return redirect(url_for('crediario_movimento_bp.list_movimentos_crediario'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar movimentação. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar movimentação: {e}', 'danger')

    return render_template('crediario_movimentos/edit.html', 
                           movimento=movimento,
                           crediarios_disponiveis=crediarios_disponiveis,
                           grupos_disponiveis=grupos_disponiveis)

@crediario_movimento_bp.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
def delete_movimento_crediario(movimento_id):
    movimento = CrediarioMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(movimento)
        db.session.commit()
        flash('Movimentação de Crediário excluída com sucesso!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir o registro. Existem itens relacionados a ele.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao excluir movimentação: {e}', 'danger')
    
    return redirect(url_for('crediario_movimento_bp.list_movimentos_crediario'))
