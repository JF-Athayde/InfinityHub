from flask import (
    render_template, redirect, url_for, flash, request,
    jsonify, current_app
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from Infinity import app, database
from Infinity.models import User, Calendar, Task, File, FlashNote
from Infinity.form import LoginForm, RegisterForm, ProfileForm, FileUploadForm, FormFlashNotes

import os
from datetime import date, datetime

# Importa funções para integração com Google Calendar
from Infinity.google_calendar import (
    add_event_to_google_calendar,
    get_google_calendar_events
)

# ======================== ROTAS PRINCIPAIS ========================

@app.route('/')
def homepage():
    # Página inicial, passa o usuário atual para a template
    return render_template('homepage.html', user=current_user)


@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    # Página de tarefas, só acessível se estiver logado

    if request.method == 'POST':
        # Ao enviar uma nova tarefa
        description = request.form.get('description', '').strip()
        if description:
            # Cria tarefa ligada ao usuário logado
            new_task = Task(
                description=description,
                user_id=current_user.id  # Importante para linkar usuário
            )
            database.session.add(new_task)
            database.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
        else:
            flash('Descrição da tarefa não pode ser vazia.', 'warning')
        return redirect(url_for('tasks'))

    # Se for GET, exibe as tarefas do usuário
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.id.desc()).all()
    return render_template('tasks.html', tasks=tasks, user=current_user)


@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    # Rota para deletar tarefa específica
    task = Task.query.get_or_404(task_id)
    database.session.delete(task)
    database.session.commit()
    flash('Tarefa excluída com sucesso!', 'success')
    return redirect(url_for('tasks'))


@app.route('/calendar')
@login_required
def calendar():
    # Página do calendário que verifica se o usuário está autenticado no Google Calendar
    google_authenticated = current_user.get_google_credentials() is not None
    return render_template('calendar.html', google_authenticated=google_authenticated, user=current_user)


@app.route('/calendar/events')
@login_required
def calendar_events():
    # Retorna os eventos salvos localmente no banco, do usuário logado, em formato JSON
    eventos = Calendar.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {
            "title": evento.title,
            "start": evento.data.isoformat(),
            "description": evento.description,
            "category": evento.category
        } for evento in eventos
    ])


@app.route('/calendar/day/<int:ano>/<int:mes>/<int:dia>')
@login_required
def events_by_day(ano, mes, dia):
    # Mostra os eventos de um dia específico no calendário local
    data = date(ano, mes, dia)
    eventos = Calendar.query.filter_by(user_id=current_user.id, day_month_year=data).all()
    return render_template('events_day.html', eventos=eventos, data=data, user=current_user)


# ======================== LOGIN E PERFIL ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Página de login - se já estiver logado, redireciona para homepage
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))

    form = LoginForm()

    if form.validate_on_submit():
        # Verifica se email existe e senha está correta
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('profile_user', username=user.username))
        else:
            flash('Email ou senha incorretos.', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Página de registro - redireciona para homepage se já estiver logado
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Cria novo usuário com senha criptografada
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        database.session.add(new_user)
        database.session.commit()
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/profile/<username>')
@login_required
def profile_user(username):
    # Página de perfil do usuário
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('homepage'))
    return render_template('profile.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Página para editar configurações do perfil
    form = ProfileForm()
    if form.validate_on_submit():
        if form.photo.data:
            # Salva foto enviada na pasta profile_pictures
            filename = secure_filename(form.photo.data.filename)
            upload_folder = os.path.join(current_app.root_path, 'static/assets/profile_pictures')
            os.makedirs(upload_folder, exist_ok=True)
            form.photo.data.save(os.path.join(upload_folder, filename))
            current_user.photo_url = filename
        # Atualiza os dados do usuário
        current_user.username = form.username.data
        current_user.cargo = form.cargo.data
        current_user.bio = form.bio.data
        database.session.commit()
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('profile_user', username=current_user.username))
    elif request.method == 'GET':
        # Preenche o formulário com os dados atuais do usuário
        form.username.data = current_user.username
        form.cargo.data = current_user.cargo
        form.bio.data = current_user.bio
    return render_template('settings.html', form=form, user=current_user)


@app.route('/flash_notes', methods=['GET', 'POST'])
@login_required
def flash_notes():
    # Página para adicionar e listar notas rápidas (flash notes)
    form = FormFlashNotes()
    if form.validate_on_submit():
        add_flash_note_for_user(current_user, form.content.data)
        flash('Nota adicionada com sucesso!', 'success')
        return redirect(url_for('flash_notes'))

    # Lista as notas do usuário (ordem decrescente e depois inverte para ordem crescente)
    notes = FlashNote.query.filter_by(user_id=current_user.id).order_by(FlashNote.timestamp.desc()).all()
    notes.reverse()
    return render_template('flash_notes.html', form=form, user=current_user, notes=notes)


@app.route('/logout')
@login_required
def logout():
    # Faz logout do usuário
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('homepage'))


# ======================== ARQUIVOS ========================

@app.route('/central_arquivos')
@login_required
def file_center():
    # Página central de arquivos compartilhados
    files = File.query.order_by(File.uploaded_at.desc()).all()
    form = FileUploadForm()
    return render_template('file_center.html', files=files, form=form, user=current_user)


@app.route('/novo_arquivo')
@login_required
def new_file():
    # Página para adicionar um novo arquivo
    form = FileUploadForm()
    return render_template('add_file.html', form=form, user=current_user)


@app.route('/file_upload', methods=['POST', 'GET'])
@login_required
def file_upload():
    # Endpoint para enviar arquivo
    form = FileUploadForm()
    if form.validate_on_submit():
        file = File(
            user_id=current_user.id,
            title=form.title.data,
            link=form.link.data,
            description=form.description.data
        )
        database.session.add(file)
        database.session.commit()
        flash('Arquivo salvo com sucesso!', 'success')
        return redirect(url_for('file_center'))
    # Caso tenha erro na validação
    files = File.query.order_by(File.uploaded_at.desc()).all()
    flash('Erro ao enviar arquivo. Verifique os campos.', 'danger')
    return render_template('file_center.html', form=form, files=files, user=current_user)


def add_flash_note_for_user(user, content):
    # Função para adicionar nota rápida para o usuário
    new_note = FlashNote(content=content, user_id=user.id, timestamp=datetime.utcnow())
    database.session.add(new_note)
    database.session.commit()

    # Limita as notas a no máximo 5, apagando as mais antigas
    notes = FlashNote.query.filter_by(user_id=user.id).order_by(FlashNote.timestamp.asc()).all()

    if len(notes) > 5:
        notes_to_delete = notes[:-5]  # todas menos as 5 últimas
        for note in notes_to_delete:
            database.session.delete(note)
        database.session.commit()
