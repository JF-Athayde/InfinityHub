from flask import (
    redirect, url_for, flash, request, session, jsonify, render_template
)
from flask_login import login_required, current_user
from Infinity import app, database
from Infinity.models import Calendar
import os
import pathlib
import json
from datetime import date, datetime, time, timedelta

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Permite usar OAuth2 sem HTTPS para desenvolvimento (não recomendado para produção)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Define o caminho do arquivo com as credenciais do cliente Google
GOOGLE_CLIENT_SECRETS_FILE = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

# Escopos necessários para acesso ao Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

# URI para onde o Google redireciona após a autenticação
REDIRECT_URI = 'http://localhost:5000/oauth2callback' # Change This

def add_event_to_google_calendar(summary, description, start_datetime, end_datetime):
    # Função para adicionar um evento no Google Calendar usando credenciais do usuário atual
    
    # Carrega as credenciais armazenadas do usuário
    creds_data = json.loads(current_user.google_credentials or '{}')
    if not creds_data:
        raise Exception("Usuário não autenticado com Google")

    # Cria objeto Credentials para API
    creds = Credentials(**creds_data)
    service = build('calendar', 'v3', credentials=creds)

    # Monta o evento a ser criado
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

    # Insere o evento na agenda principal do usuário
    created_event = service.events().insert(calendarId='primary', body=event).execute()

    # Atualiza as credenciais (token, refresh_token etc.) caso tenham sido renovadas
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


def get_google_calendar_events():
    # Função que busca os próximos eventos do Google Calendar do usuário atual
    
    if not current_user.get_google_credentials():
        # Se não autenticado, retorna None
        return None

    creds_data = json.loads(current_user.google_credentials)
    creds = Credentials(**creds_data)
    service = build('calendar', 'v3', credentials=creds)

    # Data e hora atual em formato ISO para filtrar eventos futuros
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        maxResults=20,
        timeMin=now,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    # Atualiza as credenciais caso o token tenha sido renovado
    current_user.set_google_credentials({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    })
    database.session.commit()

    # Retorna lista dos eventos
    return events_result.get('items', [])


@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    # Rota para página e envio de formulário para adicionar evento local + sincronizar com Google Calendar

    from Infinity.form import CalendarForm  # Import local para evitar problemas de importação circular
    form = CalendarForm()
    dia = request.args.get('dia')
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    # Preenche o formulário com data caso parâmetros sejam fornecidos na URL
    if dia and mes and ano:
        try:
            form.data.data = date(int(ano), int(mes), int(dia))
        except ValueError:
            pass

    if form.validate_on_submit():
        # Cria intervalo fixo de 1 hora das 10h às 11h para o evento
        data_inicio = datetime.combine(form.data.data, time(10, 0))
        data_fim = data_inicio + timedelta(hours=1)

        # Cria evento local no banco
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
            # Tenta sincronizar o evento com o Google Calendar do usuário
            add_event_to_google_calendar(
                summary=form.title.data,
                description=form.description.data,
                start_datetime=data_inicio,
                end_datetime=data_fim
            )
            flash("Evento sincronizado com o Google Calendar!", "success")
        except Exception as e:
            # Caso falhe, avisa que salvou localmente, mas não sincronizou
            print("Erro ao sincronizar com Google Calendar:", e)
            flash("Evento salvo, mas não sincronizado com o Google Calendar.", "warning")

        return redirect(url_for('calendar'))

    # Renderiza o formulário para GET
    return render_template('add_event.html', form=form, user=current_user)


@app.route('/authorize')
@login_required
def authorize():
    # Rota que inicia o fluxo de autorização OAuth2 do Google
    
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Solicita refresh token
        include_granted_scopes='false',
        prompt='consent'  # Sempre pede consentimento para garantir refresh token
    )
    # Salva o estado na sessão para segurança
    session['state'] = state
    # Redireciona usuário para página do Google para consentimento
    return redirect(authorization_url)


@app.route('/oauth2callback')
@login_required
def oauth2callback():
    # Rota que recebe o callback do Google após consentimento do usuário

    try:
        state = session.get('state')
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=REDIRECT_URI
        )
        # Finaliza a troca de token com o Google
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Salva as credenciais no banco associadas ao usuário
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
    # Redireciona para página do calendário
    return redirect(url_for('calendar'))


@app.route('/calendar/events/google')
@login_required
def calendar_events_google():
    # Rota que retorna os eventos do Google Calendar do usuário autenticado em JSON

    events = get_google_calendar_events()
    if events is None:
        # Caso usuário não tenha autenticado com Google Calendar
        return jsonify({'error': 'Não autenticado com Google Calendar'}), 401
    return jsonify([{
        'id': event.get('id'),
        'title': event.get('summary', 'Sem título'),
        'start': event['start'].get('dateTime', event['start'].get('date')),
        'end': event['end'].get('dateTime', event['end'].get('date'))
    } for event in events])
