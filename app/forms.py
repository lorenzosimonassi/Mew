#   app/forms.py

from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, PasswordField, BooleanField, SubmitField, DateField, FloatField, IntegerField, SelectField, HiddenField, DateTimeField
from wtforms.validators import Length, ValidationError, DataRequired, Email, EqualTo, Optional
import sqlalchemy as sa
import phonenumbers
from app import db
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar')
    submit = SubmitField('Logar')

class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    password2 = PasswordField('Confirmar senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')


    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Este nome já está sendo utilizado.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Este e-mail já está sendo utilizado.')

    def validate_telefone(self, telefone):
        try:
            phone = phonenumbers.parse(telefone.data, "BR")  # Altere para o país desejado
            if not phonenumbers.is_valid_number(phone):
                raise ValidationError("Número de telefone inválido.")
        except:
            raise ValidationError("Formato de telefone inválido.")

class EditProfileForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    about_me = TextAreaField('Sobre mim', validators=[Length(min=0, max=140)])
    submit = SubmitField('Enviar')

class PetForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    peso = FloatField('Peso (kg)', validators=[DataRequired()])
    sangue = StringField('Sangue', validators=[DataRequired()])
    idade = IntegerField('Idade (em anos)', validators=[DataRequired()])
    raca = StringField('Raça', validators=[DataRequired()])
    especie = StringField('Espécie', validators=[DataRequired()])
    pelagem = StringField('Pelagem', validators=[DataRequired()])
    sexo = StringField('Sexo', validators=[DataRequired()])
    submit_pet = SubmitField('Adicionar Pet')

class PagamentoForm(FlaskForm):
    data_pagamento = DateField('Data', format='%Y-%m-%d', validators=[DataRequired(message="Selecione uma data válida")])
    tipo = SelectField('Tipo de Pagamento', 
                      choices=[('', 'Selecione...'),  # Opção vazia inicial
                               ('credito', 'Cartão de Crédito'), 
                               ('debito', 'Cartão de Débito'),
                               ('pix', 'PIX'),
                               ('boleto', 'Boleto')],
                      validators=[DataRequired(message="Selecione um tipo de pagamento")])
    
    # Novos campos para cartão
    numero_cartao = StringField('Número do Cartão', validators=[Length(min=13, max=19)])
    nome_cartao = StringField('Nome no Cartão')
    codigo_seguranca = StringField('CVV/CVC', validators=[Length(min=3, max=4)])
    bandeira_cartao = SelectField('Bandeira', 
                                 choices=[('', 'Selecione...'),  # Opção vazia inicial
                                          ('visa', 'Visa'), 
                                          ('mastercard', 'MasterCard'),
                                          ('amex', 'American Express'),
                                          ('elo', 'Elo'),
                                          ('hipercard', 'Hipercard')],
                                 validators=[Optional()])  # Será validado condicionalmente

    submit_pagamento = SubmitField('Adicionar Pagamento')

    def validate(self, extra_validators=None):
        # Validação padrão primeiro
        if not super().validate():
            return False

        # Validação condicional para campos de cartão
        if self.tipo.data in ['credito', 'debito']:
            if not self.numero_cartao.data:
                self.numero_cartao.errors.append('Número do cartão é obrigatório')
                return False
            if not self.nome_cartao.data:
                self.nome_cartao.errors.append('Nome no cartão é obrigatório')
                return False
            if not self.codigo_seguranca.data:
                self.codigo_seguranca.errors.append('Código de segurança é obrigatório')
                return False
            if not self.bandeira_cartao.data:
                self.bandeira_cartao.errors.append('Selecione uma bandeira')
                return False

        return True

class VeterinarioRegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    tipo_usuario = HiddenField('Tipo', default=1)
    password = PasswordField('Senha', validators=[DataRequired()])
    password2 = PasswordField('Confirmar senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registre-se como Veterinário')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Este nome já está sendo utilizado.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Este e-mail já está sendo utilizado.')

    def validate_telefone(self, telefone):
        try:
            phone = phonenumbers.parse(telefone.data, "BR")
            if not phonenumbers.is_valid_number(phone):
                raise ValidationError("Número de telefone inválido.")
        except:
            raise ValidationError("Formato de telefone inválido.")
        
class SolicitarConsultaForm(FlaskForm):
    pet = SelectField('Pet', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Solicitar Consulta')

class PerguntaForm(FlaskForm):
    pergunta = TextAreaField('Sua Pergunta', validators=[
        DataRequired(),
        Length(min=10, max=140)
    ])
    submit = SubmitField('Enviar Pergunta')

class RespostaForm(FlaskForm):
    resposta = TextAreaField('Sua Resposta', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    submit = SubmitField('Enviar Resposta')

class SintomaForm(FlaskForm):
    sintoma_comum = SelectField('Sintoma Comum', choices=[
        ('', 'Selecione um sintoma comum'),
        ('apetite', 'Alterações no apetite'),
        ('peso', 'Perda de peso'),
        ('vomito', 'Vômitos'),
        ('diarreia', 'Diarreia'),
        ('letargia', 'Letargia'),
        ('comportamento', 'Mudanças de comportamento'),
        ('respiratorio', 'Problemas respiratórios'),
        ('pele', 'Alterações na pele'),
        ('pelagem', 'Alterações na pelagem'),
        ('olhos', 'Alterações nos olhos'),
        ('ouvidos', 'Alterações nos ouvidos'),
        ('boca', 'Alterações na boca')
    ], validators=[Optional()])
    
    outro_sintoma = StringField('Outro Sintoma', validators=[
        Optional(),
        Length(max=100)
    ])
    
    submit_sintoma = SubmitField('Adicionar Sintoma')
    
    def validate(self, extra_validators=None):
        if not super().validate():
            return False
            
        if not self.sintoma_comum.data and not self.outro_sintoma.data:
            self.sintoma_comum.errors.append('Selecione um sintoma comum ou descreva outro')
            return False
            
        return True