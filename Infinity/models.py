from Infinity import database, login_manager
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Date
import json

# Função necessária para o Flask-Login carregar o usuário logado a partir do ID salvo na sessão
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Modelo do usuário
class User(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(80), nullable=False)
    email = database.Column(database.String(120), unique=True, nullable=False)
    password_hash = database.Column(database.String(128), nullable=False)
    cargo = database.Column(database.String(50))
    bio = database.Column(database.Text)
    photo_url = database.Column(database.String(255))  # URL da foto de perfil

    # Relacionamento com FlashNote (um usuário pode ter várias notas)
    flash_notes = database.relationship('FlashNote', back_populates='user', lazy=True)

    # Campo para guardar as credenciais do Google (serializadas em JSON)
    google_credentials = database.Column(database.Text)

    # Converte o JSON salvo em objeto Python
    def get_google_credentials(self):
        if self.google_credentials:
            return json.loads(self.google_credentials)
        return None

    # Salva as credenciais como JSON
    def set_google_credentials(self, credentials):
        self.google_credentials = json.dumps(credentials)
        database.session.commit()


# Modelo de evento do calendário
class Calendar(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    user = database.relationship('User', backref='calendars')
    data = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    day_month_year = database.Column(Date, nullable=False)  # Usado para agrupar eventos por dia
    title = database.Column(database.String(100), nullable=False)
    description = database.Column(database.Text)
    category = database.Column(database.String(50), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Se 'data' for fornecida mas 'day_month_year' não, extrai a data simples
        if self.data and not self.day_month_year:
            if hasattr(self.data, 'date'):
                self.day_month_year = self.data.date()
            else:
                self.day_month_year = self.data


# Modelo de tarefas (to-do list)
class Task(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    description = database.Column(database.String(200), nullable=False)
    completed = database.Column(database.Boolean, default=False)
    created_at = database.Column(database.DateTime, default=datetime.utcnow)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)

    user = database.relationship('User', backref='tasks')  # Relacionamento com usuário


# Modelo de arquivos com links (upload via link)
class File(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    title = database.Column(database.String(120), nullable=False)
    description = database.Column(database.Text, nullable=True)
    link = database.Column(database.String(255), nullable=False)
    uploaded_at = database.Column(database.DateTime, default=datetime.utcnow)

    user = database.relationship('User', backref='files')  # Relacionamento com usuário


# Modelo de notas rápidas (flash notes)
class FlashNote(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    content = database.Column(database.String(500), nullable=False)
    timestamp = database.Column(database.DateTime, default=datetime.utcnow)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)

    # Relacionamento reverso com User (coerente com User.flash_notes)
    user = database.relationship('User', back_populates='flash_notes')
