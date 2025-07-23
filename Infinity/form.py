from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, FileField, PasswordField,
    BooleanField, DateTimeLocalField, SelectField
)
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo
from flask_wtf.file import FileAllowed

# Formulário de login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')  # Checkbox para manter login
    submit = SubmitField('Entrar')

# Formulário de registro de novo usuário
class RegisterForm(FlaskForm):
    username = StringField('Nome de usuário', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(), EqualTo('password')  # Verifica se senha confere
    ])
    submit = SubmitField('Registrar')

# Formulário de edição de perfil
class ProfileForm(FlaskForm):
    username = StringField('Nome de usuário', validators=[
        DataRequired(), Length(min=3, max=80)
    ])
    cargo = StringField('Cargo', validators=[
        Length(max=50)
    ])
    bio = TextAreaField('Biografia', validators=[
        Optional(), Length(max=500)
    ])
    photo = FileField('Foto de perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Somente imagens JPG e PNG são permitidas')
    ])
    submit = SubmitField('Salvar alterações')

# Formulário de criação de evento no calendário
class CalendarForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired()])
    description = TextAreaField("Descrição")
    data = DateTimeLocalField("Data e Hora", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    category = SelectField("Prioridade", choices=[
        ("1", "Muito Baixa"),
        ("2", "Baixa"),
        ("3", "Média"),
        ("4", "Alta"),
        ("5", "Muito Alta")
    ], validators=[DataRequired()])
    warning = BooleanField("Aviso")  # Marcar como aviso ou lembrete
    submit = SubmitField("Adicionar Evento")

# Formulário para tarefas simples
class TaskForm(FlaskForm):
    description = StringField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Adicionar')

# Formulário para upload de links de arquivos
class FileUploadForm(FlaskForm):
    title = StringField('Título do Arquivo', validators=[
        DataRequired(), Length(max=150)
    ])
    link = StringField('Link do Arquivo', validators=[
        DataRequired(), Length(max=300)
    ])
    description = TextAreaField('Descrição', validators=[
        Optional(), Length(max=500)
    ])
    submit = SubmitField('Salvar Arquivo')

# Formulário para criar notas rápidas (tipo post-it)
class FormFlashNotes(FlaskForm):
    content = StringField('Nota', validators=[DataRequired()])
    submit = SubmitField('Adicionar')
