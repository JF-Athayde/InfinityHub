document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('calendar');

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: ''
    },
    events: "/calendar/events",
    eventClassNames: function(arg) {
      // Define classes baseadas na categoria para colorir
      let cat = arg.event.extendedProps.category?.toLowerCase() || 'outro';
      return ['fc-event-categoria-' + cat];
    },
    eventDidMount: function(info) {
      // Tooltip no hover mostrando descrição
      if (info.event.extendedProps.description) {
        let tooltip = document.createElement('div');
        tooltip.className = 'event-tooltip';
        tooltip.textContent = info.event.extendedProps.description;

        info.el.addEventListener('mouseenter', function(e) {
          document.body.appendChild(tooltip);
          tooltip.style.top = (e.pageY + 5) + 'px';
          tooltip.style.left = (e.pageX + 5) + 'px';
        });

        info.el.addEventListener('mousemove', function(e) {
          tooltip.style.top = (e.pageY + 5) + 'px';
          tooltip.style.left = (e.pageX + 5) + 'px';
        });

        info.el.addEventListener('mouseleave', function() {
          tooltip.remove();
        });
      }
    },
    eventContent: function(arg) {
      // Customiza o conteúdo do evento para mostrar só o título (sem bola)
      return { html: arg.event.title };
    },
    dayMaxEvents: 3 // mostra no máximo 3 eventos por dia, depois "+X"
  });

  calendar.render();
});
