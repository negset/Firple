document.addEventListener('DOMContentLoaded', () => {
  const main = document.querySelector('main');
  const navHeight = window.getComputedStyle(document.querySelector('nav'))['height'];
  const footerHeight = window.getComputedStyle(document.querySelector('footer'))['height'];
  main.style.minHeight = `calc(100vh - ${navHeight} - ${footerHeight})`;

  const navbarBurger = document.querySelector('.navbar-burger');
  const burgerTarget = document.getElementById(navbarBurger.dataset.target);
  navbarBurger.onclick = () => {
    navbarBurger.classList.toggle('is-active');
    burgerTarget.classList.toggle('is-active');
  };
  main.onclick = () => {
    navbarBurger.classList.remove('is-active');
    burgerTarget.classList.remove('is-active');
  };

  const textArea = document.querySelector('.sample-text');
  const subfamily = document.getElementById('subfamily');
  subfamily.onchange = e => {
    const v = e.target.value;
    textArea.style.fontStyle = (v == 'regular' || v == 'bold') ? 'normal' : 'italic';
    textArea.style.fontWeight = (v == 'regular' || v == 'italic') ? 400 : 700;
  };
  const weight = document.getElementById('weight');
  weight.value = parseInt(window.getComputedStyle(textArea)['fontSize']);
  weight.oninput = e => {
    textArea.style.fontSize = e.target.value + 'px';
  };
  const ligature = document.getElementById('ligature');
  ligature.oninput = e => {
    textArea.style.fontVariantLigatures = e.target.checked ? "normal" : "none";
  };
});