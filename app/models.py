#   app/models.py

from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import validates
from hashlib import md5
import phonenumbers

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[Optional[str]] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    telefone: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20), index=True, unique=True)
        # Relacionamentos existentes (ex.: posts)
    posts: so.Mapped[list["Post"]] = so.relationship("Post", back_populates="author", lazy='dynamic')
    tipo_usuario: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, nullable=False)
    pets: so.Mapped[list["Pet"]] = so.relationship("Pet", back_populates="owner", lazy='dynamic')
    pagamentos: so.Mapped[list["Pagamento"]] = so.relationship("Pagamento", back_populates="user", lazy='dynamic')
    consultas: so.Mapped[list["Consulta"]] = so.relationship("Consulta", back_populates="user", foreign_keys="Consulta.user_id")

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    posts: so.Mapped[list["Post"]] = so.relationship(
        "Post", 
        back_populates="author", 
        foreign_keys="Post.user_id",  # Especifica explicitamente qual FK usar
        lazy='dynamic'
    )
    
    # Mantenha as outras relações
    consultas_cliente: so.Mapped[list["Consulta"]] = so.relationship(
        "Consulta", 
        foreign_keys="Consulta.user_id", 
        back_populates="user",
        lazy='dynamic'
    )
    
    consultas_veterinario: so.Mapped[list["Consulta"]] = so.relationship(
        "Consulta", 
        foreign_keys="Consulta.vet_id", 
        back_populates="veterinario",
        lazy='dynamic'
    )

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda:datetime.now(timezone.utc))

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    estado: so.Mapped[str] = so.mapped_column(sa.String(20), default='Não Respondido')
    resposta: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    
    # Relacionamentos com foreign keys explícitas
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    vet_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('user.id'))
    
    author: so.Mapped[User] = so.relationship(
        "User", 
        back_populates="posts", 
        foreign_keys=[user_id]  # Especifica qual FK usar
    )
    veterinario: so.Mapped[Optional[User]] = so.relationship(
        "User", 
        foreign_keys=[vet_id]
    )

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    #users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE, Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name

class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

class Pet(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    nome: so.Mapped[str] = so.mapped_column(sa.String(64))
    peso: so.Mapped[float] = so.mapped_column(sa.Float)  # Ex: 5.7 (kg)
    sangue: so.Mapped[str] = so.mapped_column(sa.String(10))
    idade: so.Mapped[int] = so.mapped_column(sa.Integer)
    raca: so.Mapped[str] = so.mapped_column(sa.String(64))
    especie: so.Mapped[str] = so.mapped_column(sa.String(64))
    pelagem: so.Mapped[str] = so.mapped_column(sa.String(64))
    sexo: so.Mapped[str] = so.mapped_column(sa.String(10))
    sintomas: so.Mapped[list["Sintoma"]] = so.relationship("Sintoma", back_populates="pet", lazy='dynamic')
    
    # Chave estrangeira para User
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))
    owner: so.Mapped[User] = so.relationship("User", back_populates="pets")
    
    def __repr__(self):
        return f"<Pet {self.nome}>"

class Pagamento(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    data: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now, index=True)
    tipo: so.Mapped[str] = so.mapped_column(sa.String(50))
    numero_cartao: so.Mapped[Optional[str]] = so.mapped_column(sa.String(19))
    nome_cartao: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    codigo_seguranca: so.Mapped[Optional[str]] = so.mapped_column(sa.String(4))
    bandeira_cartao: so.Mapped[Optional[str]] = so.mapped_column(sa.String(20))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))
    user: so.Mapped["User"] = so.relationship("User", back_populates="pagamentos")

    def __repr__(self):
        return f"<Pagamento {self.tipo} em {self.data}>"
    
class Consulta(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    estado: so.Mapped[str] = so.mapped_column(sa.String(20), default='Aguardando')
    horario: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now)
    
    # Relacionamento com User (cliente)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'))
    user: so.Mapped["User"] = so.relationship("User", foreign_keys=[user_id], back_populates="consultas_cliente")
    
    # Relacionamento com Pet
    pet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('pet.id'))
    pet: so.Mapped["Pet"] = so.relationship("Pet")
    
    # Relacionamento com Veterinário
    vet_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('user.id'))
    veterinario: so.Mapped[Optional["User"]] = so.relationship("User", foreign_keys=[vet_id], back_populates="consultas_veterinario")

class Sintoma(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    descricao: so.Mapped[str] = so.mapped_column(sa.String(100))
    tipo: so.Mapped[str] = so.mapped_column(sa.String(20), default='comum')  # 'comum' ou 'outro'
    pet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('pet.id'))
    data_registro: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    
    pet: so.Mapped["Pet"] = so.relationship("Pet", back_populates="sintomas")