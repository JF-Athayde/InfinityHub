// Aguarda o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggle-dark'); // Botão de alternância (switch)
    const body = document.body; // Referência ao <body>

    // Verifica o tema salvo anteriormente no localStorage
    const savedTheme = localStorage.getItem('theme');

    if (savedTheme === 'dark') {
        body.classList.remove('light');
        body.classList.add('dark');
        toggle.checked = true; // Marca o botão como ativado
    } else {
        body.classList.remove('dark');
        body.classList.add('light');
        toggle.checked = false; // Deixa o botão desmarcado
    }

    // Adiciona evento ao botão para alternar o tema
    toggle.addEventListener('change', () => {
        if (toggle.checked) {
            // Se o botão estiver ativado, aplica tema escuro
            body.classList.remove('light');
            body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            // Se estiver desativado, aplica tema claro
            body.classList.remove('dark');
            body.classList.add('light');
            localStorage.setItem('theme', 'light');
        }
    });
});
