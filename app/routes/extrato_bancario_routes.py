# app/routes/extrato_bancario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from datetime import datetime
from sqlalchemy import func
from decimal import Decimal # <--- IMPORTAR DECIMAL

extrato_bancario_bp = Blueprint('extrato_bancario_bp', __name__, template_folder='../templates/extratos_bancarios')

# --- Rota para Selecionar Mês e Conta para o Extrato ---
@extrato_bancario_bp.route('/selecionar', methods=['GET'])
@login_required
def selecionar_extrato():
    contas_disponiveis = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco, Conta.conta).all()
    return render_template('extratos_bancarios/selecionar.html', contas_disponiveis=contas_disponiveis)

# --- Rota para Exibir o Extrato Bancário ---
@extrato_bancario_bp.route('/exibir', methods=['POST'])
@login_required
def exibir_extrato():
    conta_id = request.form.get('conta_id')
    mes_ano_str = request.form.get('mes_ano') # Formato YYYY-MM

    if not (conta_id and mes_ano_str):
        flash('Por favor, selecione uma conta e um mês/ano.', 'danger')
        return redirect(url_for('extrato_bancario_bp.selecionar_extrato'))

    try:
        conta_id = int(conta_id)
        mes_ano_dt = datetime.strptime(mes_ano_str, '%Y-%m').date().replace(day=1)
        
        proximo_mes_dt = mes_ano_dt.replace(month=mes_ano_dt.month % 12 + 1, day=1)
        if proximo_mes_dt.month == 1:
            proximo_mes_dt = proximo_mes_dt.replace(year=mes_ano_dt.year + 1)

    except ValueError:
        flash('Mês/Ano ou Conta inválidos.', 'danger')
        return redirect(url_for('extrato_bancario_bp.selecionar_extrato'))

    conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first()
    if not conta:
        flash('Conta não encontrada ou você não tem permissão para acessá-la.', 'danger')
        return redirect(url_for('extrato_bancario_bp.selecionar_extrato'))

    # 1. Calcular Saldo Inicial do Mês
    # Começa com o saldo inicial da conta (que já é Decimal)
    saldo_inicial_calculado = conta.saldo_inicial 

    # Soma/subtrai movimentos ANTES do mês selecionado para esta conta
    movimentos_anteriores = ContaMovimento.query.join(
        ContaTransacao, ContaMovimento.conta_transacao_id == ContaTransacao.id
    ).filter(
        ContaMovimento.conta_id == conta.id,
        ContaMovimento.data < mes_ano_dt
    ).all()

    for mov in movimentos_anteriores:
        # Garante que a operação seja entre Decimais
        if mov.conta_transacao_item.tipo == 'Crédito':
            saldo_inicial_calculado += mov.valor # mov.valor já é Decimal
        elif mov.conta_transacao_item.tipo == 'Débito':
            saldo_inicial_calculado -= mov.valor # mov.valor já é Decimal
    
    saldo_inicial = saldo_inicial_calculado


    # 2. Obter Movimentações do Mês Selecionado
    movimentos_do_mes = ContaMovimento.query.join(
        ContaTransacao, ContaMovimento.conta_transacao_id == ContaTransacao.id
    ).filter(
        ContaMovimento.conta_id == conta.id,
        ContaMovimento.data >= mes_ano_dt,
        ContaMovimento.data < proximo_mes_dt
    ).order_by(ContaMovimento.data, ContaMovimento.data_criacao).all()

    # 3. Calcular Saldo Final do Mês
    saldo_final = saldo_inicial # saldo_inicial já é Decimal
    for mov in movimentos_do_mes:
        # Garante que a operação seja entre Decimais
        if mov.conta_transacao_item.tipo == 'Crédito':
            saldo_final += mov.valor # mov.valor já é Decimal
        elif mov.conta_transacao_item.tipo == 'Débito':
            saldo_final -= mov.valor # mov.valor já é Decimal

    return render_template('extratos_bancarios/extrato.html',
                           conta=conta,
                           mes_ano=mes_ano_dt,
                           saldo_inicial=saldo_inicial,
                           movimentos=movimentos_do_mes,
                           saldo_final=saldo_final)
