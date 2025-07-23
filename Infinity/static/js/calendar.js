// Aguarda o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function () {
    // Referência ao contêiner onde os dias serão renderizados
    const numbersDaysContainer = document.querySelector('.numbers-days');
    // Label do mês e ano atual
    const monthYearLabel = document.getElementById('month-year');
    // Botões de navegação entre meses
    const prevBtn = document.getElementById('prev-month');
    const nextBtn = document.getElementById('next-month');

    // Data atual (ponto de partida do calendário)
    let currentDate = new Date();

    // Função assíncrona para buscar os eventos do servidor
    async function fetchEvents(year, month) {
        try {
            const response = await fetch('/calendar/events'); // Requisição para obter eventos
            if (!response.ok) throw new Error('Erro ao buscar eventos');
            const allEvents = await response.json();

            // Filtra apenas os eventos do mês e ano atual
            return allEvents.filter(event => {
                const eventDate = new Date(event.start);
                return eventDate.getFullYear() === year && eventDate.getMonth() === month;
            });
        } catch (error) {
            console.error(error);
            return []; // Retorna array vazio em caso de erro
        }
    }

    // Função para renderizar o calendário do mês atual
    async function renderCalendar(date) {
        numbersDaysContainer.innerHTML = ''; // Limpa os dias atuais

        const year = date.getFullYear();
        const month = date.getMonth();

        const monthNames = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];

        // Atualiza o título com o nome do mês e ano
        monthYearLabel.textContent = `${monthNames[month]} ${year}`;

        // Determina o dia da semana do primeiro dia do mês
        let firstDay = new Date(year, month, 1).getDay();
        firstDay = (firstDay + 6) % 7; // Ajusta para segunda-feira = 0

        // Número de dias no mês atual
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Busca eventos do mês
        const events = await fetchEvents(year, month);

        // Agrupa eventos por dia do mês
        const eventsByDay = new Map();
        events.forEach(event => {
            const day = new Date(event.start).getDate();
            if (!eventsByDay.has(day)) {
                eventsByDay.set(day, []);
            }
            eventsByDay.get(day).push(event);
        });

        // Renderiza espaços vazios antes do primeiro dia
        for (let i = 0; i < firstDay; i++) {
            const emptySpan = document.createElement('span');
            emptySpan.classList.add('empty-day');
            numbersDaysContainer.appendChild(emptySpan);
        }

        // Renderiza os dias do mês com os eventos
        for (let day = 1; day <= daysInMonth; day++) {
            const span = document.createElement('span');
            span.setAttribute('data-day', day);

            const dayEvents = eventsByDay.get(day) || [];

            // Ordena os eventos pela categoria (prioridade)
            dayEvents.sort((a, b) => Number(b.category) - Number(a.category));

            // Junta os títulos dos eventos do dia
            const titles = dayEvents.map(e => e.title).join(', ');
            // Define a classe de prioridade (ex: priority-1, priority-2...)
            const priorityClass = dayEvents.length ? `priority-${dayEvents[0].category}` : '';

            if (priorityClass) {
                span.classList.add(priorityClass);
            }

            // Cria o número do dia
            const dayNumberDiv = document.createElement('div');
            dayNumberDiv.classList.add('day-number');
            dayNumberDiv.textContent = day;

            // Cria o título dos eventos
            const eventTitleDiv = document.createElement('div');
            eventTitleDiv.classList.add('event-title');
            eventTitleDiv.textContent = titles;

            // Adiciona os elementos ao span principal do dia
            span.appendChild(dayNumberDiv);
            span.appendChild(eventTitleDiv);

            // Adiciona evento de clique para redirecionar
            span.addEventListener('click', () => {
                if (dayEvents.length > 0) {
                    // Vai para página do dia com eventos
                    window.location.href = `/calendar/day/${year}/${month + 1}/${day}`;
                } else {
                    // Vai para página de adicionar evento
                    window.location.href = `/add_event?dia=${day}&mes=${month + 1}&ano=${year}`;
                }
            });

            numbersDaysContainer.appendChild(span);
        }
    }

    // Navegar para o mês anterior
    prevBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });

    // Navegar para o próximo mês
    nextBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });

    // Renderiza o calendário na inicialização
    renderCalendar(currentDate);
});
