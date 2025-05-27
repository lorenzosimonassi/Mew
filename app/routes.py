# app/routes.py

from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timezone
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PetForm, PagamentoForm, VeterinarioRegistrationForm, SolicitarConsultaForm, RespostaForm, PerguntaForm, SintomaForm
from app.models import User, Pet, Pagamento, Consulta, Post, Sintoma

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    
    return render_template("index.html", title='Pagina inicial')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title="Login Page", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            telefone=form.telefone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='EditProfile', form=form)

@app.route('/profile_items', methods=['GET', 'POST'])
@login_required
def profile_items():
    pet_form = PetForm()
    pagamento_form = PagamentoForm()
    sintoma_form = SintomaForm()  # Novo formulário

    # Processa envio do formulário de Pet
    if pet_form.submit_pet.data and pet_form.validate_on_submit():
        new_pet = Pet(
            nome=pet_form.nome.data,
            peso=pet_form.peso.data,
            sangue=pet_form.sangue.data,
            idade=pet_form.idade.data,
            raca=pet_form.raca.data,
            especie=pet_form.especie.data,
            pelagem=pet_form.pelagem.data,
            sexo=pet_form.sexo.data,
            user_id=current_user.id
        )
        db.session.add(new_pet)
        db.session.commit()
        flash('Pet adicionado com sucesso!', 'success')
        return redirect(url_for('profile_items'))

    # Processa envio do formulário de Pagamento
    if pagamento_form.submit_pagamento.data and pagamento_form.validate_on_submit():
        new_pagamento = Pagamento(
            data=pagamento_form.data_pagamento.data,
            tipo=pagamento_form.tipo.data,
            numero_cartao=pagamento_form.numero_cartao.data if pagamento_form.tipo.data in ['credito', 'debito'] else None,
            nome_cartao=pagamento_form.nome_cartao.data if pagamento_form.tipo.data in ['credito', 'debito'] else None,
            codigo_seguranca=pagamento_form.codigo_seguranca.data if pagamento_form.tipo.data in ['credito', 'debito'] else None,
            bandeira_cartao=pagamento_form.bandeira_cartao.data if pagamento_form.tipo.data in ['credito', 'debito'] else None,
            user_id=current_user.id
        )
        db.session.add(new_pagamento)
        db.session.commit()
        flash('Pagamento registrado com sucesso!', 'success')
        return redirect(url_for('profile_items'))
    
    if sintoma_form.submit_sintoma.data and sintoma_form.validate_on_submit():
        pet_id = request.form.get('pet_id')
        pet = Pet.query.filter_by(id=pet_id, user_id=current_user.id).first_or_404()
        
        if sintoma_form.sintoma_comum.data:
            descricao = dict(sintoma_form.sintoma_comum.choices).get(sintoma_form.sintoma_comum.data)
            tipo = 'comum'
        else:
            descricao = sintoma_form.outro_sintoma.data
            tipo = 'outro'
        
        novoSintoma = Sintoma(
            descricao=descricao,
            tipo=tipo,
            pet_id=pet.id
        )
        db.session.add(novoSintoma)
        db.session.commit()
        flash('Sintoma adicionado com sucesso!', 'success')
        return redirect(url_for('profile_items'))


    # Recupera os registros do usuário logado
    pets = current_user.pets.order_by(Pet.nome.asc()).all()
    pagamentos = current_user.pagamentos.order_by(Pagamento.data.desc()).all()

    return render_template('profile_items.html',
                         pet_form=pet_form,
                         pagamento_form=pagamento_form,
                         sintoma_form=sintoma_form,  # Novo formulário
                         pets=pets,
                         pagamentos=pagamentos,
                         Sintoma=Sintoma)

@app.route('/register_vet', methods=['GET', 'POST'])
def register_vet():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = VeterinarioRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            telefone=form.telefone.data,
            tipo_usuario=1  # Força o tipo como veterinário
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registro como veterinário concluído!')
        return redirect(url_for('login'))
    
    return render_template('register_vet.html', form=form)

@app.route('/solicitar_consulta', methods=['GET', 'POST'])
@login_required
def solicitar_consulta():
    if current_user.tipo_usuario == 1:  # Veterinários não podem solicitar
        return redirect(url_for('index'))
    
    form = SolicitarConsultaForm()
    form.pet.choices = [(pet.id, pet.nome) for pet in current_user.pets.all()]
    
    if form.validate_on_submit():
        consulta = Consulta(
            user_id=current_user.id,
            pet_id=form.pet.data,
            horario=datetime.now(),
            estado='Aguardando'
        )
        db.session.add(consulta)
        db.session.commit()
        flash('Consulta solicitada com sucesso!', 'success')
        return redirect(url_for('minhas_consultas'))
    
    return render_template('solicitar_consulta.html', form=form)

@app.route('/minhas_consultas')
@login_required
def minhas_consultas():
    if current_user.tipo_usuario == 1:  # Veterinário
        consultas = current_user.consultas_veterinario.filter_by(estado='Aguardando').all()
    else:  # Cliente
        consultas = current_user.consultas_cliente.all()
    return render_template('minhas_consultas.html', consultas=consultas)

@app.route('/aceitar_consulta/<int:consulta_id>')
@login_required
def aceitar_consulta(consulta_id):
    if current_user.tipo_usuario != 1:  # Só veterinários podem aceitar
        return redirect(url_for('index'))
    
    consulta = Consulta.query.get_or_404(consulta_id)
    consulta.estado = 'Aceito'
    consulta.vet_id = current_user.id
    db.session.commit()
    flash('Consulta aceita com sucesso!', 'success')
    return redirect(url_for('consultas_pendentes'))

@app.route('/consultas_pendentes')
@login_required
def consultas_pendentes():
    if current_user.tipo_usuario != 1:
        return redirect(url_for('index'))
    
    # Mostra tanto as pendentes quanto as aceitas pelo veterinário
    consultas = Consulta.query.filter(
        (Consulta.estado == 'Aguardando') | 
        ((Consulta.estado == 'Aceito') & (Consulta.vet_id == current_user.id))
    ).order_by(Consulta.estado, Consulta.horario).all()
    
    return render_template('consultas_pendentes.html', consultas=consultas)


@app.route('/avaliacoes')
@login_required
def avaliacoes():
    if current_user.tipo_usuario != 1:  # Apenas para veterinários
        flash('Esta página é apenas para veterinários', 'error')
        return redirect(url_for('index'))
    
    return render_template('avaliacoes_vet.html')

@app.route('/faq', methods=['GET', 'POST'])
def faq():
    # Verifica se é veterinário para mostrar o formulário de resposta
    resposta_form = RespostaForm() if current_user.is_authenticated and current_user.tipo_usuario == 1 else None
    
    # Lógica para enviar resposta
    if resposta_form and resposta_form.validate_on_submit():
        post_id = request.form.get('post_id')
        post = Post.query.get_or_404(post_id)
        post.resposta = resposta_form.resposta.data
        post.estado = 'Respondido'
        post.vet_id = current_user.id
        db.session.commit()
        flash('Resposta enviada com sucesso!', 'success')
        return redirect(url_for('faq'))
    
    # Pega todas as perguntas ordenadas por data
    perguntas = Post.query.order_by(Post.timestamp.desc()).all()
    
    return render_template('faq.html', 
                         perguntas=perguntas,
                         resposta_form=resposta_form)

@app.route('/perguntar', methods=['GET', 'POST'])
@login_required
def perguntar():
    if current_user.tipo_usuario == 1:  # Veterinários não podem perguntar
        flash('Veterinários não podem fazer perguntas.', 'warning')
        return redirect(url_for('faq'))
    
    form = PerguntaForm()
    if form.validate_on_submit():
        post = Post(
            body=form.pergunta.data,
            author=current_user,
            estado='Não Respondido'
        )
        db.session.add(post)
        db.session.commit()
        flash('Pergunta enviada com sucesso!', 'success')
        return redirect(url_for('faq'))
    
    return render_template('perguntar.html', form=form)

@app.route('/parcerias')
def parcerias():
    # Lista de lojas parceiras (pode vir do banco de dados no futuro)
    lojas_parceiras = [
        {
            'nome': 'PetShop Amigo Fiel',
            'logo': '/static/images/petshop.jpg',
            'desconto': '15%',
            'categoria': 'Alimentos e Acessórios'
        },
        {
            'nome': 'VetCare Clínica',
            'logo': '/static/images/clinica.jpg',
            'desconto': '10% em consultas',
            'categoria': 'Serviços Veterinários'
        },
        {
            'nome': 'PetStyle',
            'logo': '/static/images/petstyle.jpg',
            'desconto': '20% em banho e tosa',
            'categoria': 'Estética Animal'
        }
    ]
    return render_template('parcerias.html', lojas=lojas_parceiras, title='Nossos Parceiros')