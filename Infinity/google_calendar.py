# Importações necessárias do Flask
from flask import (
    redirect, url_for, flash, request, session, jsonify, render_template
)

# Importações do Flask-Login e app/modelos do projeto
from flask_login import login_required, current_user
from Infinity import app, database
from Infinity.models import Calendar

# Bibliotecas padrão
import os
import pathlib
import json
from datetime import date, datetime, time, timedelta

# Bibliotecas do Google para autenticação e acesso ao Calendar
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Permite uso de HTTP ao invés de HTTPS no ambiente de desenvolvimento
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Define o caminho para o arquivo de credenciais do Google
GOOGLE_CLIENT_SECRETS_FILE = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

# Escopos de acesso ao Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

# URL de redirecionamento após autenticação do Google
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# Função que adiciona um evento ao Google Calendar do usuário logado
def add_event_to_google_calendar(summary, description, start_datetime, end_datetime):
    # Obtém as credenciais salvas do usuário (formato JSON)
    creds_data = json.loads(current_user.google_credentials or '{}')
    if not creds_data:
        raise Exception("Usuário não autenticado com Google")

    # Constrói o objeto de credenciais do Google
    creds = Credentials(**creds_data)

    # Tenta renovar token se estiver expirado e tiver refresh_token
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Cria serviço da API do Google Calendar
    service = build('calendar', 'v3', credentials=creds)

    # Define o evento com título, descrição e horário
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

    # Insere o evento no calendário do usuário
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print("Evento criado no Google Calendar:", created_event)

    # Atualiza credenciais (caso tenham mudado)
    current_user.set_google_credentials({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    })
    database.session.commit()

    return created_event

# Função que recupera eventos do Google Calendar do usuário
def get_google_calendar_events(credentials):
    # Cria serviço do Google Calendar com as credenciais fornecidas
    service = build('calendar', 'v3', credentials=credentials)

    # Define intervalo fixo de busca (de 01 a 31 de julho de 2025)
    start = datetime(2025, 7, 1).isoformat() + 'Z'
    end = datetime(2025, 7, 31, 23, 59, 59).isoformat() + 'Z'

    # Busca eventos do Google Calendar no intervalo especificado
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    # Retorna a lista de eventos (ou lista vazia se nenhum encontrado)
    return events_result.get('items', [])

# Rota para adicionar evento localmente e no Google Calendar
@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    # Importa o formulário localmente para evitar importação circular
    from Infinity.form import CalendarForm
    form = CalendarForm()

    # Pega data passada pela URL (opcional)
    dia = request.args.get('dia')
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    # Se data completa foi passada na URL, tenta preencher o campo automaticamente
    if dia and mes and ano:
        try:
            form.data.data = date(int(ano), int(mes), int(dia))
        except ValueError:
            pass  # Ignora datas inválidas

    # Se o formulário foi enviado corretamente
    if form.validate_on_submit():
        # Define horário fixo das 10h às 11h
        data_inicio = datetime.combine(form.data.data, time(10, 0))
        data_fim = data_inicio + timedelta(hours=1)

        # Cria evento local no banco de dados
        novo_evento = Calendar(
            user_id=current_user.id,
            data=form.data.data,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data
        )
        database.session.add(novo_evento)
        database.session.commit()

        # Tenta sincronizar com Google Calendar
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

        # Redireciona para a página principal do calendário
        return redirect(url_for('calendar'))

    # Renderiza o template com o formulário
    return render_template('add_event.html', form=form, user=current_user)

# Rota que inicia o fluxo de autorização com o Google
@app.route('/authorize')
@login_required
def authorize():
    # Cria o fluxo de OAuth com as credenciais do client
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    # Cria URL de autorização com escopo offline (para refresh token)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='false',
        prompt='consent'
    )

    # Salva o estado da sessão (medida de segurança)
    session['state'] = state

    # Redireciona usuário para consentimento no Google
    return redirect(authorization_url)

# Rota chamada após o usuário consentir no Google (callback)
@app.route('/oauth2callback')
@login_required
def oauth2callback():
    try:
        # Recupera o estado salvo da sessão
        state = session.get('state')

        # Cria novamente o fluxo com os mesmos dados
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=REDIRECT_URI
        )

        # Troca o código de autorização por um token de acesso
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Salva as credenciais do usuário no banco
        current_user.set_google_credentials({
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        })

        database.session.commit()
        flash('Google Calendar conectado com sucesso!', 'success')
    except Exception as e:
        flash(f"Erro ao conectar Google Calendar: {e}", 'danger')

    # Redireciona para o calendário
    return redirect(url_for('calendar'))

# Rota que retorna os eventos do Google Calendar do usuário autenticado
@app.route('/calendar/events/google')
@login_required
def calendar_events_google():
    # Obtém as credenciais salvas do usuário
    creds_data = current_user.get_google_credentials()
    if not creds_data:
        # Usuário não autenticado com Google
        return jsonify({'error': 'Não autenticado com Google Calendar'}), 401

    # Constrói objeto de credenciais
    credentials = Credentials(**creds_data)

    # Se as credenciais estiverem expiradas e tiver refresh_token, renova
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    # Busca os eventos no Google Calendar
    events = get_google_calendar_events(credentials)

    # Retorna os eventos formatados em JSON
    return jsonify([{
        'id': event.get('id'),
        'title': event.get('summary', 'Sem título'),
        'start': event['start'].get('dateTime', event['start'].get('date')),
        'end': event['end'].get('dateTime', event['end'].get('date'))
    } for event in events])
