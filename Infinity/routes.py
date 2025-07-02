from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from Infinity import app, database
from Infinity.models import User, Calendar
from Infinity.form import LoginForm, RegisterForm, ProfileForm, CalendarForm
from werkzeug.utils import secure_filename
from flask import current_app
import os
from flask import jsonify

@app.route('/')
def homepage():
    return render_template('homepage.html', user=current_user)

@app.route("/infinity_app")
def infinity_app():
    return render_template("infinity_app.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route('/notes')
@login_required
def notes():
    return render_template('notes.html')

@app.route('/tasks')
@login_required
def tasks():
    return render_template('tasks.html')

@app.route('/calendar')
@login_required
def calendar():
    # Página apenas mostra o calendário visual
    return render_template('calendar.html', user=current_user)

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    form = CalendarForm()

    # Pré-preencher o campo de data se dia/mes/ano forem passados na URL
    dia = request.args.get('dia')
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    if dia and mes and ano:
        try:
            from datetime import date
            data_preenchida = date(int(ano), int(mes), int(dia))
            form.data.data = data_preenchida
        except ValueError:
            pass  # ignora se a data for inválida

    if form.validate_on_submit():
        novo_evento = Calendar(
            user_id=current_user.id,
            data=form.data.data,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            warning=form.warning.data or False
        )
        database.session.add(novo_evento)
        database.session.commit()
        flash("Evento adicionado!", "success")
        return redirect(url_for('calendar'))

    return render_template('add_event.html', form=form, user=current_user)

@app.route('/calendar/events')
@login_required
def calendar_events():
    eventos = Calendar.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        "title": evento.title,
        "start": evento.data.isoformat(),
        "description": evento.description,
        "category": evento.category
    } for evento in eventos])

@app.route('/calendar/day/<int:ano>/<int:mes>/<int:dia>')
@login_required
def events_by_day(ano, mes, dia):
    from datetime import date
    data = date(ano, mes, dia)
    eventos = Calendar.query.filter_by(user_id=current_user.id, day_month_year=data).all()
    
    return render_template('events_day.html', eventos=eventos, data=data, user=current_user)

@app.route('/profile/<username>')
@login_required
def profile_user(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('homepage'))

    return render_template('profile.html', user=user)

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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('homepage'))
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

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ProfileForm()

    if form.validate_on_submit():
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)

            upload_folder = os.path.join(current_app.root_path, 'static', 'assets', 'profile_pictures')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            form.photo.data.save(file_path)
            current_user.photo_url = filename  # salvar só o nome do arquivo no banco

        current_user.username = form.username.data
        current_user.cargo = form.cargo.data
        current_user.bio = form.bio.data

        database.session.commit()
        flash('Configurações atualizadas com sucesso!', 'success')
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
