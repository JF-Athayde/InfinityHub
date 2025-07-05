from flask import (
    render_template, redirect, url_for, flash, request, session,
    jsonify, current_app
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from Infinity import app, database
from Infinity.models import User, Calendar, Task, File
from Infinity.form import LoginForm, RegisterForm, ProfileForm, CalendarForm, FileUploadForm

import os
import pathlib
from datetime import date, datetime, time, timedelta

# Google OAuth2
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

GOOGLE_CLIENT_SECRETS_FILE = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# ======================== ROTAS PRINCIPAIS ========================

@app.route('/')
def homepage():
    return render_template('homepage.html', user=current_user)

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if description:
            # Cria nova tarefa associada ao usuário logado
            new_task = Task(
                description=description,
                user_id=current_user.id  # <- ESSENCIAL!
            )
            database.session.add(new_task)
            database.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
        else:
            flash('Descrição da tarefa não pode ser vazia.', 'warning')
        return redirect(url_for('tasks'))

    # GET: lista tarefas do usuário logado
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.id.desc()).all()
    return render_template('tasks.html', tasks=tasks, user=current_user)

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    database.session.delete(task)
    database.session.commit()
    flash('Tarefa excluída com sucesso!', 'success')
    return redirect(url_for('tasks'))

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html', user=current_user)

@app.route('/calendar/events')
@login_required
def calendar_events():
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
    data = date(ano, mes, dia)
    eventos = Calendar.query.filter_by(user_id=current_user.id, day_month_year=data).all()
    return render_template('events_day.html', eventos=eventos, data=data, user=current_user)

# ======================== LOGIN E PERFIL ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = LoginForm()
    if form.validate_on_submit():
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
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = RegisterForm()
    if form.validate_on_submit():
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
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('homepage'))
    return render_template('profile.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            upload_folder = os.path.join(current_app.root_path, 'static/assets/profile_pictures')
            os.makedirs(upload_folder, exist_ok=True)
            form.photo.data.save(os.path.join(upload_folder, filename))
            current_user.photo_url = filename
        current_user.username = form.username.data
        current_user.cargo = form.cargo.data
        current_user.bio = form.bio.data
        database.session.commit()
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('profile_user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.cargo.data = current_user.cargo
        form.bio.data = current_user.bio
    return render_template('settings.html', form=form, user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('homepage'))

# ======================== ARQUIVOS ========================

@app.route('/central_arquivos')
@login_required
def file_center():
    files = File.query.order_by(File.uploaded_at.desc()).all()
    form = FileUploadForm()
    return render_template('file_center.html', files=files, form=form, user=current_user)

@app.route('/novo_arquivo')
@login_required
def new_file():
    form = FileUploadForm()
    return render_template('add_file.html', form=form, user=current_user)

@app.route('/file_upload', methods=['POST', 'GET'])
@login_required
def file_upload():
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
    files = File.query.order_by(File.uploaded_at.desc()).all()
    flash('Erro ao enviar arquivo. Verifique os campos.', 'danger')
    return render_template('file_center.html', form=form, files=files, user=current_user)

# ======================== EVENTOS + GOOGLE CALENDAR ========================

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    form = CalendarForm()
    dia = request.args.get('dia')
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    if dia and mes and ano:
        try:
            form.data.data = date(int(ano), int(mes), int(dia))
        except ValueError:
            pass

    if form.validate_on_submit():
        # Define horário fixo, exemplo: 10:00 até 11:00
        data_inicio = datetime.combine(form.data.data, time(10, 0))
        data_fim = data_inicio + timedelta(hours=1)
        novo_evento = Calendar(
            user_id=current_user.id,
            data=form.data.data,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data
        )
        database.session.add(novo_evento)
        database.session.commit()

        try:
            add_event_to_google_calendar(
                summary=form.title.data,
                description=form.description.data,
                start_datetime=data_inicio,
                end_datetime=data_fim
            )
            flash("Evento sincronizado com o Google Calendar!", "success")
        except Exception as e:
            print("Erro ao sincronizar com Google Calendar:", e)
            flash("Evento salvo, mas não sincronizado com o Google Calendar.", "warning")

        return redirect(url_for('calendar'))

    return render_template('add_event.html', form=form, user=current_user)

@app.route('/authorize')
@login_required
def authorize():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='false',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
@login_required
def oauth2callback():
    try:
        state = session.get('state')
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        flash('Google Calendar conectado com sucesso!', 'success')
    except Exception as e:
        flash(f"Erro ao conectar Google Calendar: {e}", 'danger')
    return redirect(url_for('calendar'))

@app.route('/calendar/events/google')
@login_required
def calendar_events_google():
    events = get_google_calendar_events()
    if events is None:
        return jsonify({'error': 'Não autenticado com Google Calendar'}), 401
    return jsonify([{
        'id': event.get('id'),
        'title': event.get('summary', 'Sem título'),
        'start': event['start'].get('dateTime', event['start'].get('date')),
        'end': event['end'].get('dateTime', event['end'].get('date'))
    } for event in events])

def get_google_calendar_events():
    if 'credentials' not in session:
        return None
    creds = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=creds)
    now = '2023-01-01T00:00:00Z'
    events_result = service.events().list(
        calendarId='primary',
        maxResults=20,
        timeMin=now,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return events_result.get('items', [])

def add_event_to_google_calendar(summary, description, start_datetime, end_datetime):
    if 'credentials' not in session:
        return False

    creds = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
    }

    print("Evento a ser enviado:", event)

    created = service.events().insert(calendarId='primary', body=event).execute()
    print("Evento criado:", created)

    return created
