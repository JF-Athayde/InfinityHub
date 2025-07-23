// Função assíncrona para buscar e exibir eventos do Google Calendar
async function syncGoogleEvents() {
    try {
        // Faz a requisição para o backend
        const response = await fetch('/calendar/events/google');

        // Se o usuário não estiver autenticado (erro 401), não faz nada
        if (response.status === 401) {
            return;
        }

        // Converte a resposta em JSON
        const events = await response.json();

        // Seleciona o contêiner onde os eventos serão exibidos
        const container = document.getElementById('googleEventsContainer');
        // Limpa e insere o título da seção
        container.innerHTML = '<h2>Eventos do Google Calendar:</h2>';

        // Para cada evento retornado, cria um elemento na página
        events.forEach(event => {
            const start = new Date(event.start).toLocaleString(); // Formata a data

            const div = document.createElement('div');
            div.className = 'google-event';
            div.innerHTML = `<strong>${event.title}</strong><br>Data: ${start}`;

            // Adiciona o evento no contêiner
            container.appendChild(div);
        });

    } catch (error) {
        // Em caso de erro, apenas exibe uma mensagem simples
        console.log('Ok');
    }
}

// Ao carregar a página...
window.onload = () => {
    syncGoogleEvents(); // Sincroniza os eventos ao carregar
    setInterval(syncGoogleEvents, 60000); // E repete a sincronização a cada 1 minuto
};
