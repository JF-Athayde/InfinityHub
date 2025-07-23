// Função para alternar o menu responsivo (abre/fecha)
function toggleMenu(x) {
    // Alterna a classe "active" no botão (geralmente o ícone de menu)
    x.classList.toggle("active");

    // Alterna a classe "open" na lista de links de navegação
    document.querySelector('.nav-links').classList.toggle("open");
}
