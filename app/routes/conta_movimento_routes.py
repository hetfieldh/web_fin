# app/routes/conta_movimento_routes.py
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_model import Conta 
from app.models.conta_transacao_model import ContaTransacao
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def standardize_name(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

conta_movimento_bp = Blueprint('conta_movimento_bp', __name__, template_folder='../templates/conta_movimentos')

@conta_movimento_bp.route('/')
@login_required
def list_movimentos():
    movimentos = ContaMovimento.query.filter_by(usuario_id=current_user.id).order_by(ContaMovimento.data.desc(), ContaMovimento.data_criacao.desc()).all()
    return render_template('conta_movimentos/list.html', movimentos=movimentos)

@conta_movimento_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_movimento():
    contas_disponiveis = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco, Conta.conta).all()
    tipos_transacao_disponiveis = ContaTransacao.query.filter_by(usuario_id=current_user.id).order_by(ContaTransacao.transacao).all()

    if request.method == 'POST':
        conta_id = request.form.get('conta_id')
        conta_transacao_id = request.form.get('conta_transacao_id')
        data_str = request.form.get('data')
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        if not (conta_id and conta_transacao_id and data_str and valor_str):
            flash('Por favor, preencha todos os campos obrigatórios (Conta, Transação, Data, Valor).', 'danger')
            return render_template('conta_movimentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)

        try:
            conta_id = int(conta_id)
            transacao_id = int(conta_transacao_id)
            
            conta_obj = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first()
            transacao_obj = ContaTransacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first()

            if not conta_obj:
                flash('Conta bancária inválida selecionada.', 'danger')
                return render_template('conta_movimentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_transacao_disponiveis=tipos_transacao_disponiveis)
            if not transacao_obj:
                flash('Tipo de transação inválido selecionado.', 'danger')
                return render_template('conta_movimentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        except ValueError:
            flash('IDs de Conta ou Transação inválidos.', 'danger')
            return render_template('conta_movimentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida. Use o formato YYYY-MM-DD.', 'danger')
            return render_template('conta_movimentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('conta_movimentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        except ValueError:
            flash('Valor deve ser um número válido.', 'danger')
            return render_template('conta_movimentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('conta_movimentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)

        new_movimento = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_id,
            conta_transacao_id=transacao_id,
            data=data,
            valor=valor,
            descricao=descricao
        )
        try:
            db.session.add(new_movimento)
            db.session.commit()
            flash('Movimento bancário adicionado com sucesso!', 'success')
            return redirect(url_for('conta_movimento_bp.list_movimentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao adicionar movimento. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar movimento: {e}', 'danger')

    return render_template('conta_movimentos/add.html', 
                           contas_disponiveis=contas_disponiveis,
                           tipos_transacao_disponiveis=tipos_transacao_disponiveis)

@conta_movimento_bp.route('/edit/<int:movimento_id>', methods=['GET', 'POST'])
@login_required
def edit_movimento(movimento_id):
    movimento = ContaMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()
    
    contas_disponiveis = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco, Conta.conta).all()
    tipos_transacao_disponiveis = ContaTransacao.query.filter_by(usuario_id=current_user.id).order_by(ContaTransacao.transacao).all()

    if request.method == 'POST':
        valor_str = request.form.get('valor')
        descricao = request.form.get('descricao')

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('Valor deve ser um número positivo (maior que zero).', 'danger')
                return render_template('conta_movimentos/edit.html', 
                                       movimento=movimento,
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        except ValueError:
            flash('Valor deve ser um número válido.', 'danger')
            return render_template('conta_movimentos/edit.html', 
                                   movimento=movimento,
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        
        movimento.valor = valor

        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('conta_movimentos/edit.html', 
                                   movimento=movimento,
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_transacao_disponiveis=tipos_transacao_disponiveis)
        
        movimento.descricao = descricao

        try:
            db.session.commit()
            flash('Movimento bancário atualizado com sucesso!', 'success')
            return redirect(url_for('conta_movimento_bp.list_movimentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar movimento. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar movimento: {e}', 'danger')

    return render_template('conta_movimentos/edit.html', 
                           movimento=movimento,
                           contas_disponiveis=contas_disponiveis,
                           tipos_transacao_disponiveis=tipos_transacao_disponiveis)

@conta_movimento_bp.route('/delete/<int:movimento_id>', methods=['POST'])
@login_required
def delete_movimento(movimento_id):
    movimento = ContaMovimento.query.filter_by(id=movimento_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(movimento)
        db.session.commit()
        flash('Movimento bancário excluído com sucesso!', 'success')
    except IntegrityError: 
        db.session.rollback()
        flash('Não foi possível excluir o registro. Existem itens relacionados a ele.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao excluir movimento: {e}', 'danger')
    
    return redirect(url_for('conta_movimento_bp.list_movimentos'))
