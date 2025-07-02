document.addEventListener('DOMContentLoaded', function () {
    const numbersDaysContainer = document.querySelector('.numbers-days');
    const monthYearLabel = document.getElementById('month-year');
    const prevBtn = document.getElementById('prev-month');
    const nextBtn = document.getElementById('next-month');

    let currentDate = new Date();

    async function fetchEvents(year, month) {
        try {
            const response = await fetch('/calendar/events');
            if (!response.ok) throw new Error('Erro ao buscar eventos');
            const allEvents = await response.json();
            // Filtrar eventos do mês/ano
            return allEvents.filter(event => {
                const eventDate = new Date(event.start);
                return eventDate.getFullYear() === year && eventDate.getMonth() === month;
            });
        } catch (error) {
            console.error(error);
            return [];
        }
    }

    async function renderCalendar(date) {
        numbersDaysContainer.innerHTML = '';

        const year = date.getFullYear();
        const month = date.getMonth();

        const monthNames = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];
        monthYearLabel.textContent = `${monthNames[month]} ${year}`;

        // Corrigir: no JS, getDay() domingo=0 ... sábado=6
        // Queremos segunda=0 ... domingo=6
        let firstDay = new Date(year, month, 1).getDay();
        firstDay = (firstDay + 6) % 7; // Ajuste para segunda = 0

        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const events = await fetchEvents(year, month);
        const eventsByDay = new Map();

        events.forEach(event => {
            const day = new Date(event.start).getDate();
            if (!eventsByDay.has(day)) {
                eventsByDay.set(day, []);
            }
            eventsByDay.get(day).push(event);
        });

        // Espaços vazios antes do primeiro dia
        for (let i = 0; i < firstDay; i++) {
            const emptySpan = document.createElement('span');
            emptySpan.classList.add('empty-day');
            numbersDaysContainer.appendChild(emptySpan);
        }

        // Dias do mês
        for (let day = 1; day <= daysInMonth; day++) {
            const span = document.createElement('span');
            span.setAttribute('data-day', day);

            const dayEvents = eventsByDay.get(day) || [];
            dayEvents.sort((a, b) => Number(b.category) - Number(a.category));

            const titles = dayEvents.map(e => e.title).join(', ');
            const priorityClass = dayEvents.length ? `priority-${dayEvents[0].category}` : '';

            if (priorityClass) {
                span.classList.add(priorityClass);
            }

            const dayNumberDiv = document.createElement('div');
            dayNumberDiv.classList.add('day-number');
            dayNumberDiv.textContent = day;

            const eventTitleDiv = document.createElement('div');
            eventTitleDiv.classList.add('event-title');
            eventTitleDiv.textContent = titles;

            span.appendChild(dayNumberDiv);
            span.appendChild(eventTitleDiv);

            span.addEventListener('click', () => {
                if (dayEvents.length > 0) {
                    // Vai para a página do dia com eventos
                    window.location.href = `/calendar/day/${year}/${month + 1}/${day}`;
                } else {
                    // Vai para adicionar evento já preenchido com a data
                    window.location.href = `/add_event?dia=${day}&mes=${month + 1}&ano=${year}`;
                }
            });

            numbersDaysContainer.appendChild(span);
        }
    }

    prevBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });

    nextBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });

    renderCalendar(currentDate);
});
