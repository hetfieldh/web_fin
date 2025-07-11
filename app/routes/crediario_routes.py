# app/routes/crediario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.crediario_model import Crediario, tipo_crediario_enum
from sqlalchemy.exc import IntegrityError
import re # Para validações de formato

# Criação do Blueprint para as rotas de crediário
crediario_bp = Blueprint('crediario_bp', __name__, template_folder='../templates/crediarios')

# --- Rota para Listar Crediários ---
@crediario_bp.route('/')
@login_required
def list_crediarios():
    # Apenas listar os crediários do usuário logado
    crediarios = Crediario.query.filter_by(usuario_id=current_user.id).order_by(Crediario.crediario).all()
    # Explicitamente especifica o caminho completo do template
    return render_template('crediarios/list.html', crediarios=crediarios)

# --- Rota para Adicionar Novo Crediário ---
@crediario_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_crediario():
    # Obtém os valores possíveis para o ENUM 'tipo'
    tipos_crediario = tipo_crediario_enum.enums

    if request.method == 'POST':
        crediario_nome = request.form.get('crediario')
        tipo_from_form = request.form.get('tipo')
        final = request.form.get('final')
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        # --- Validações ---
        if not (crediario_nome and tipo_from_form):
            flash('Por favor, preencha os campos obrigatórios (Nome do Crediário, Tipo).', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        # Validação do Nome do Crediário
        crediario_nome_stripped = crediario_nome.strip()
        if not crediario_nome_stripped:
            flash('O nome do crediário não pode ser vazio.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        if len(crediario_nome_stripped) < 3:
            flash('O nome do crediário deve ter no mínimo 3 caracteres.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        
        # DEBUG: Imprime o valor da string antes da validação regex
        print(f"DEBUG: crediario_nome_stripped para validação: '{crediario_nome_stripped}'") 

        # ALTERADO: Expressão regular para permitir letras (incluindo acentuadas), números, espaços, &, . e -
        # O ^[a-zA-Z0-9À-ÿ] garante que comece com letra/número/acentuado
        # O resto permite letras, números, espaços, &, ponto literal, hífen e acentuados
        # Removido \p{L} e \p{N} que causam PatternError
        if not re.fullmatch(r'^[a-zA-Z0-9À-ÿ][a-zA-Z0-9\s&.\-À-ÿ]*$', crediario_nome_stripped):
            flash('O nome do crediário deve começar com letra, número ou caractere acentuado e conter apenas letras, números, espaços, &, ., - ou caracteres acentuados.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        crediario_nome = crediario_nome_stripped # Atualiza a variável com o valor validado

        # Validação do Tipo de Crediário (ENUM)
        tipo_to_save = None
        if tipo_from_form in tipos_crediario:
            tipo_to_save = tipo_from_form
        
        if tipo_to_save is None:
            flash('Tipo de crediário inválido selecionado.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        # Validação do campo Final (opcional, mas se preenchido, validar)
        if final: # Se o campo 'final' foi preenchido
            final_stripped = final.strip()
            if not final_stripped: # Se foi preenchido apenas com espaços
                flash('O campo "Final" não pode ser apenas espaços em branco.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            if not final_stripped.isdigit(): # Deve conter apenas números
                flash('O campo "Final" deve conter apenas números.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            if len(final_stripped) != 4: # Deve ter exatamente 4 números
                flash('O campo "Final" deve conter exatamente 4 números.', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
            final = final_stripped # Atualiza a variável com o valor validado
        else:
            final = None # Garante que seja None se o campo estiver vazio, para nullable=True no DB
        
        # Validação de Limite (numérico e > 0)
        try:
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite <= 0:
                flash('Limite deve ser um valor positivo (maior que zero).', 'danger')
                return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        except ValueError:
            flash('Limite deve ser um número válido.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)
        
        # Validação de Descrição (tamanho máximo)
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediarios/add.html', tipos_crediario=tipos_crediario)

        # --- Criação e Persistência do Crediário ---
        new_crediario = Crediario(
            usuario_id=current_user.id,
            crediario=crediario_nome,
            tipo=tipo_to_save,
            final=final, # Usa o valor validado (None ou string)
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

# --- Rota para Editar Crediário ---
@crediario_bp.route('/edit/<int:crediario_id>', methods=['GET', 'POST'])
@login_required
def edit_crediario(crediario_id):
    crediario = Crediario.query.filter_by(id=crediario_id, usuario_id=current_user.id).first_or_404()
    tipos_crediario = tipo_crediario_enum.enums

    if request.method == 'POST':
        # Campos não editáveis via POST (Nome do Crediário, Tipo)
        # O campo 'final' agora é editável

        final = request.form.get('final') # Pega o valor do campo Final
        limite_str = request.form.get('limite')
        descricao = request.form.get('descricao')

        # Validação do campo Final (opcional, mas se preenchido, validar)
        if final: # Se o campo 'final' foi preenchido
            final_stripped = final.strip()
            if not final_stripped: # Se foi preenchido apenas com espaços
                flash('O campo "Final" não pode ser apenas espaços em branco.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            if not final_stripped.isdigit(): # Deve conter apenas números
                flash('O campo "Final" deve conter apenas números.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            if len(final_stripped) != 4: # Deve ter exatamente 4 números
                flash('O campo "Final" deve conter exatamente 4 números.', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
            crediario.final = final_stripped # Atualiza o objeto Crediario com o valor validado
        else:
            crediario.final = None # Garante que seja None se o campo estiver vazio
        
        # Validação de Limite (numérico e > 0)
        try:
            limite = float(limite_str.replace(',', '.')) if limite_str else 0.00
            if limite <= 0:
                flash('Limite deve ser um valor positivo (maior que zero).', 'danger')
                return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
        except ValueError:
            flash('Limite deve ser um número válido.', 'danger')
            return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)
        
        crediario.limite = limite # Atribui o limite

        # Validação de Descrição (tamanho máximo)
        if descricao and len(descricao) > 255:
            flash('A descrição não pode ter mais de 255 caracteres.', 'danger')
            return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)

        crediario.descricao = descricao # Atribui a descrição

        try:
            db.session.commit()
            flash('Crediário atualizado com sucesso!', 'success')
            return redirect(url_for('crediario_bp.list_crediarios'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro de integridade ao atualizar crediário. Verifique os dados.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar crediário: {e}', 'danger')

    return render_template('crediarios/edit.html', crediario=crediario, tipos_crediario=tipos_crediario)

# --- Rota para Excluir Crediário ---
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
