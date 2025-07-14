# app/routes/financiamento_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.financiamento_model import Financiamento, tipo_amortizacao_enum
from app.models.conta_model import Conta # Para selecionar a conta
from app.models.financiamento_parcela_model import FinanciamentoParcela, status_parcela_enum # Para importar parcelas
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import re
import csv # Para ler arquivos CSV
from io import StringIO # Para lidar com o conteúdo do arquivo em memória

# Função auxiliar para padronizar nomes (remover especiais, espaços extras, maiúsculas)
def standardize_name(name):
    if not name:
        return ""
    # Remove caracteres que não são letras, números, espaços, &, ., - (e acentuados)
    cleaned_name = re.sub(r'[^\w\s&.\-]+', '', name, flags=re.UNICODE)
    # Remove espaços múltiplos e espaços nas extremidades, depois converte para maiúsculas
    return re.sub(r'\s+', ' ', cleaned_name).strip().upper()

# Criação do Blueprint para as rotas de financiamentos
financiamento_bp = Blueprint('financiamento_bp', __name__, template_folder='../templates/financiamentos')

# --- Rota para Listar Financiamentos ---
@financiamento_bp.route('/')
@login_required
def list_financiamentos():
    # Apenas listar os financiamentos do usuário logado
    financiamentos = Financiamento.query.filter_by(usuario_id=current_user.id).order_by(Financiamento.data_criacao.desc()).all()
    return render_template('financiamentos/list.html', financiamentos=financiamentos)

# --- Rota para Adicionar Novo Financiamento ---
@financiamento_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_financiamento():
    contas_disponiveis = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco, Conta.conta).all()
    tipos_amortizacao = tipo_amortizacao_enum.enums

    if request.method == 'POST':
        conta_id = request.form.get('conta_id')
        nome_financiamento = request.form.get('nome_financiamento')
        banco = request.form.get('banco') # Este campo não está no modelo DBML, mas está no formulário
        valor_total_financiado_str = request.form.get('valor_total_financiado')
        taxa_juros_anual_str = request.form.get('taxa_juros_anual')
        data_inicio_str = request.form.get('data_inicio')
        prazo_meses_str = request.form.get('prazo_meses')
        tipo_amortizacao_from_form = request.form.get('tipo_amortizacao')
        descricao = request.form.get('descricao')

        # --- Validações ---
        if not (conta_id and nome_financiamento and valor_total_financiado_str and 
                taxa_juros_anual_str and data_inicio_str and prazo_meses_str and tipo_amortizacao_from_form):
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)

        # 1. Validação do ID da Conta
        try:
            conta_id = int(conta_id)
            conta_obj = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first()
            if not conta_obj:
                flash('Conta bancária inválida selecionada.', 'danger')
                return render_template('financiamentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_amortizacao=tipos_amortizacao)
        except ValueError:
            flash('ID de Conta inválido.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        
        # 2. Padronização e Validação do Nome do Financiamento
        nome_financiamento_standardized = standardize_name(nome_financiamento)
        if not nome_financiamento_standardized:
            flash('O nome do financiamento não pode ser vazio.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        if len(nome_financiamento_standardized) < 3:
            flash('O nome do financiamento deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', nome_financiamento_standardized):
            flash('O nome do financiamento deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        nome_financiamento = nome_financiamento_standardized

        # 3. Validação de Valores Numéricos
        try:
            valor_total_financiado = float(valor_total_financiado_str.replace(',', '.'))
            if valor_total_financiado <= 0:
                flash('Valor Total Financiado deve ser um número positivo (maior que zero).', 'danger')
                return render_template('financiamentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_amortizacao=tipos_amortizacao)

            taxa_juros_anual = float(taxa_juros_anual_str.replace(',', '.'))
            if taxa_juros_anual < 0:
                flash('Taxa de Juros Anual não pode ser negativa.', 'danger')
                return render_template('financiamentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_amortizacao=tipos_amortizacao)

            prazo_meses = int(prazo_meses_str)
            if prazo_meses <= 0:
                flash('Prazo em Meses deve ser um número inteiro positivo (maior que zero).', 'danger')
                return render_template('financiamentos/add.html', 
                                       contas_disponiveis=contas_disponiveis,
                                       tipos_amortizacao=tipos_amortizacao)
        except ValueError:
            flash('Valores numéricos inválidos (Valor Financiado, Taxa de Juros, Prazo).', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)

        # 4. Validação de Data de Início
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de Início inválida. Use o formato YYYY-MM-DD.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)

        # 5. Validação do Tipo de Amortização (ENUM)
        tipo_amortizacao_to_save = None
        if tipo_amortizacao_from_form in tipos_amortizacao:
            tipo_amortizacao_to_save = tipo_amortizacao_from_form
        
        if tipo_amortizacao_to_save is None:
            flash('Tipo de Amortização inválido selecionado.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        
        # 6. Validação de Descrição (tamanho máximo)
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('financiamentos/add.html', 
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)

        # --- Criação e Persistência do Financiamento ---
        new_financiamento = Financiamento(
            usuario_id=current_user.id,
            conta_id=conta_id,
            nome_financiamento=nome_financiamento,
            valor_total_financiado=valor_total_financiado,
            taxa_juros_anual=taxa_juros_anual,
            data_inicio=data_inicio,
            prazo_meses=prazo_meses,
            tipo_amortizacao=tipo_amortizacao_to_save,
            descricao=descricao
        )
        try:
            db.session.add(new_financiamento)
            db.session.commit()
            flash('Financiamento adicionado com sucesso! Agora você pode importar as parcelas via CSV.', 'success')
            return redirect(url_for('financiamento_bp.list_financiamentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Já existe um financiamento com esse nome para este usuário.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar financiamento: {e}', 'danger')

    return render_template('financiamentos/add.html', 
                           contas_disponiveis=contas_disponiveis,
                           tipos_amortizacao=tipos_amortizacao)

# --- Rota para Editar Financiamento ---
@financiamento_bp.route('/edit/<int:financiamento_id>', methods=['GET', 'POST'])
@login_required
def edit_financiamento(financiamento_id):
    financiamento = Financiamento.query.filter_by(id=financiamento_id, usuario_id=current_user.id).first_or_404()
    
    contas_disponiveis = Conta.query.filter_by(usuario_id=current_user.id).order_by(Conta.nome_banco, Conta.conta).all()
    tipos_amortizacao = tipo_amortizacao_enum.enums

    if request.method == 'POST':
        # Campos editáveis: descrição
        descricao = request.form.get('descricao')

        # Validação de Descrição (tamanho máximo)
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('financiamentos/edit.html', 
                                   financiamento=financiamento,
                                   contas_disponiveis=contas_disponiveis,
                                   tipos_amortizacao=tipos_amortizacao)
        
        financiamento.descricao = descricao

        try:
            db.session.commit()
            flash('Financiamento atualizado com sucesso!', 'success')
            return redirect(url_for('financiamento_bp.list_financiamentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar financiamento. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar financiamento: {e}', 'danger')

    return render_template('financiamentos/edit.html', 
                           financiamento=financiamento,
                           contas_disponiveis=contas_disponiveis,
                           tipos_amortizacao=tipos_amortizacao)

# --- Rota para Excluir Financiamento ---
@financiamento_bp.route('/delete/<int:financiamento_id>', methods=['POST'])
@login_required
def delete_financiamento(financiamento_id):
    financiamento = Financiamento.query.filter_by(id=financiamento_id, usuario_id=current_user.id).first_or_404()

    try:
        db.session.delete(financiamento)
        db.session.commit() # Parcelas serão excluídas em cascata devido ao cascade="all, delete-orphan" no modelo FinanciamentoParcela
        flash('Financiamento excluído com sucesso!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Não foi possível excluir o registro. Existem itens relacionados a ele.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro inesperado ao excluir financiamento: {e}', 'danger')
    
    return redirect(url_for('financiamento_bp.list_financiamentos'))

# --- Rota para Importar Parcelas de Financiamento via CSV ---
@financiamento_bp.route('/importar_parcelas_csv/<int:financiamento_id>', methods=['GET', 'POST'])
@login_required
def importar_parcelas_financiamento_csv(financiamento_id):
    financiamento = Financiamento.query.filter_by(id=financiamento_id, usuario_id=current_user.id).first_or_404()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith('.csv'):
            flash('Formato de arquivo inválido. Por favor, envie um arquivo CSV.', 'danger')
            return redirect(request.url)
        
        stream = StringIO(file.stream.read().decode("UTF8"))
        csv_reader = csv.reader(stream)
        header = next(csv_reader) # Pula o cabeçalho

        required_headers = ['numero_parcela', 'data_vencimento', 'valor_principal', 'valor_juros', 'valor_seguro', 'valor_taxas', 'valor_total_previsto']
        if not all(h in header for h in required_headers):
            flash(f'Cabeçalho CSV inválido. As colunas obrigatórias são: {", ".join(required_headers)}.', 'danger')
            return render_template('financiamentos/importar_parcelas_csv.html', financiamento=financiamento)

        imported_count = 0
        errors = []

        for i, row in enumerate(csv_reader):
            row_dict = dict(zip(header, row))
            
            try:
                numero_parcela = int(row_dict['numero_parcela'])
                data_vencimento_str = row_dict['data_vencimento']
                valor_principal_str = row_dict['valor_principal']
                valor_juros_str = row_dict['valor_juros']
                valor_seguro_str = row_dict.get('valor_seguro', '0.00') # Opcional
                valor_taxas_str = row_dict.get('valor_taxas', '0.00') # Opcional
                valor_total_previsto_str = row_dict['valor_total_previsto']

                # Validação de datas
                try:
                    data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"Linha {i+2}: Formato de Data de Vencimento inválido '{data_vencimento_str}'. Use YYYY-MM-DD.")
                    continue

                # Validação de valores numéricos
                try:
                    valor_principal = float(valor_principal_str.replace(',', '.'))
                    valor_juros = float(valor_juros_str.replace(',', '.'))
                    valor_seguro = float(valor_seguro_str.replace(',', '.'))
                    valor_taxas = float(valor_taxas_str.replace(',', '.'))
                    valor_total_previsto = float(valor_total_previsto_str.replace(',', '.'))

                    if valor_principal < 0 or valor_juros < 0 or valor_seguro < 0 or valor_taxas < 0 or valor_total_previsto <= 0:
                        errors.append(f"Linha {i+2}: Valores numéricos devem ser positivos e Valor Total Previsto maior que zero.")
                        continue
                except ValueError:
                    errors.append(f"Linha {i+2}: Valores numéricos inválidos.")
                    continue
                
                # Verifica se a parcela já existe (para evitar duplicatas em re-importações)
                existing_parcela = FinanciamentoParcela.query.filter_by(
                    financiamento_id=financiamento.id,
                    numero_parcela=numero_parcela
                ).first()

                if existing_parcela:
                    # Se a parcela já existe, pode-se optar por atualizar ou pular
                    # Por simplicidade, vamos pular e registrar um erro/aviso
                    errors.append(f"Linha {i+2}: Parcela {numero_parcela} para este financiamento já existe. Pulando.")
                    continue

                new_parcela = FinanciamentoParcela(
                    financiamento_id=financiamento.id,
                    numero_parcela=numero_parcela,
                    data_vencimento=data_vencimento,
                    valor_principal=valor_principal,
                    valor_juros=valor_juros,
                    valor_seguro=valor_seguro,
                    valor_taxas=valor_taxas,
                    valor_total_previsto=valor_total_previsto,
                    status='A Pagar' # Status inicial ao importar
                )
                db.session.add(new_parcela)
                imported_count += 1

            except Exception as e:
                errors.append(f"Linha {i+2}: Erro ao processar: {e}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            if imported_count > 0:
                flash(f'{imported_count} parcelas importadas com sucesso para o financiamento "{financiamento.nome_financiamento}"!', 'success')
            if errors:
                for err in errors:
                    flash(err, 'danger')
            return redirect(url_for('financiamento_bp.list_financiamentos'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade: Algumas parcelas já existem ou há duplicatas no CSV. Nenhuma parcela foi importada.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro geral ao salvar parcelas: {e}', 'danger')

    return render_template('financiamentos/importar_parcelas_csv.html', financiamento=financiamento)

# --- Rota para Listar Parcelas de um Financiamento ---
@financiamento_bp.route('/<int:financiamento_id>/parcelas')
@login_required
def list_parcelas_financiamento(financiamento_id):
    financiamento = Financiamento.query.filter_by(id=financiamento_id, usuario_id=current_user.id).first_or_404()
    parcelas = FinanciamentoParcela.query.filter_by(financiamento_id=financiamento.id).order_by(FinanciamentoParcela.numero_parcela).all()
    return render_template('financiamentos/list_parcelas.html', financiamento=financiamento, parcelas=parcelas)

# --- Rota para Marcar Parcela como Paga ---
@financiamento_bp.route('/parcela/<int:parcela_id>/pagar', methods=['POST'])
@login_required
def pagar_parcela(parcela_id):
    parcela = FinanciamentoParcela.query.filter_by(id=parcela_id).join(
        Financiamento, FinanciamentoParcela.financiamento_id == Financiamento.id
    ).filter(
        Financiamento.usuario_id == current_user.id
    ).first_or_404()

    if parcela.status == 'Paga':
        flash('Esta parcela já está paga.', 'info')
    else:
        try:
            parcela.data_pagamento = datetime.now().date()
            parcela.valor_pago = parcela.valor_total_previsto # Assume que o valor pago é o previsto
            parcela.status = 'Paga'
            db.session.commit()
            flash(f'Parcela {parcela.numero_parcela} do financiamento "{parcela.financiamento.nome_financiamento}" marcada como paga!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao marcar parcela como paga: {e}', 'danger')
    
    return redirect(url_for('financiamento_bp.list_parcelas_financiamento', financiamento_id=parcela.financiamento_id))

