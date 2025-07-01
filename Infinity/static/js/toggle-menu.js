document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggle-dark');
    const body = document.body;

    // Checa tema salvo no localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.remove('light');
        body.classList.add('dark');
        toggle.checked = true;
    } else {
        body.classList.remove('dark');
        body.classList.add('light');
        toggle.checked = false;
    }

    // Evento de clique no botão
    toggle.addEventListener('change', () => {
        if (toggle.checked) {
            body.classList.remove('light');
            body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark');
            body.classList.add('light');
            localStorage.setItem('theme', 'light');
        }
    });
});
