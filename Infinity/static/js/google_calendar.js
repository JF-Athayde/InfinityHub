async function syncGoogleEvents() {
  try {
    const response = await fetch('/calendar/events/google');
    if (response.status === 401) {
      alert('Por favor, conecte-se ao Google Calendar primeiro clicando em "Conectar ao Google Calendar".');
      return;
    }
    const events = await response.json();

    const container = document.getElementById('googleEventsContainer');
    container.innerHTML = '<h2>Eventos do Google Calendar:</h2>';

    events.forEach(event => {
      const start = new Date(event.start).toLocaleString();

      const div = document.createElement('div');
      div.className = 'google-event';
      div.innerHTML = `<strong>${event.title}</strong><br>Data: ${start}`;
      container.appendChild(div);
    });

  } catch (error) {
    console.log('Ok')
  }
}

window.onload = () => {
  syncGoogleEvents(); // Sincroniza ao carregar
  setInterval(syncGoogleEvents, 3000); // Sincroniza a cada 5 min
};
