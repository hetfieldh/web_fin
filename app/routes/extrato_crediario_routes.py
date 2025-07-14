# app/routes/extrato_crediario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from datetime import datetime
from sqlalchemy import and_
from decimal import Decimal 

extrato_crediario_bp = Blueprint('extrato_crediario_bp', __name__, template_folder='../templates/extratos_crediarios')

@extrato_crediario_bp.route('/selecionar', methods=['GET'])
@login_required
def selecionar_extrato_crediario():
    crediarios_disponiveis = Crediario.query.filter_by(usuario_id=current_user.id).order_by(Crediario.crediario).all()
    return render_template('extratos_crediarios/selecionar.html', crediarios_disponiveis=crediarios_disponiveis)

@extrato_crediario_bp.route('/exibir', methods=['POST'])
@login_required
def exibir_extrato_crediario():
    crediario_id = request.form.get('crediario_id')
    mes_ano_str = request.form.get('mes_ano')

    if not mes_ano_str:
        flash('Por favor, selecione um mês/ano.', 'danger')
        return redirect(url_for('extrato_crediario_bp.selecionar_extrato_crediario'))

    try:
        mes_ano_dt = datetime.strptime(mes_ano_str, '%Y-%m').date().replace(day=1)
        
        proximo_mes_dt = mes_ano_dt.replace(month=mes_ano_dt.month % 12 + 1, day=1)
        if proximo_mes_dt.month == 1:
            proximo_mes_dt = proximo_mes_dt.replace(year=mes_ano_dt.year + 1)

    except ValueError:
        flash('Mês/Ano inválido. Use o formato YYYY-MM.', 'danger')
        return redirect(url_for('extrato_crediario_bp.selecionar_extrato_crediario'))

    query = CrediarioParcela.query.join(
        CrediarioMovimento, CrediarioParcela.crediario_movimento_id == CrediarioMovimento.id
    ).join(
        Crediario, CrediarioMovimento.crediario_id == Crediario.id
    ).filter(
        Crediario.usuario_id == current_user.id,
        CrediarioParcela.vencimento >= mes_ano_dt,
        CrediarioParcela.vencimento < proximo_mes_dt
    )

    crediario_selecionado = None
    if crediario_id and crediario_id != 'all':
        try:
            crediario_id = int(crediario_id)
            crediario_selecionado = Crediario.query.filter_by(id=crediario_id, usuario_id=current_user.id).first()
            if not crediario_selecionado:
                flash('Crediário não encontrado ou você não tem permissão para acessá-lo.', 'danger')
                return redirect(url_for('extrato_crediario_bp.selecionar_extrato_crediario'))
            query = query.filter(Crediario.id == crediario_id)
        except ValueError:
            flash('ID de Crediário inválido.', 'danger')
            return redirect(url_for('extrato_crediario_bp.selecionar_extrato_crediario'))
    
    parcelas_do_mes = query.order_by(CrediarioParcela.vencimento, CrediarioParcela.numero_parcela).all() 

    total_parcelas = Decimal('0.00')
    for parcela in parcelas_do_mes:
        total_parcelas += parcela.valor_parcela 

    return render_template('extratos_crediarios/extrato.html',
                           mes_ano=mes_ano_dt,
                           crediario_selecionado=crediario_selecionado,
                           parcelas=parcelas_do_mes,
                           total_parcelas=total_parcelas) 
