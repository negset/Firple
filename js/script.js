document.addEventListener('DOMContentLoaded', () => {
  const main = document.querySelector('.main');
  const navHeight = window.getComputedStyle(document.querySelector('nav'))['height'];
  const footerHeight = window.getComputedStyle(document.querySelector('.footer'))['height'];
  main.style.minHeight = `calc(100vh - ${navHeight} - ${footerHeight})`;

  const navbarBurger = document.querySelector('.navbar-burger');
  const burgerTarget = document.getElementById(navbarBurger.dataset.target);
  navbarBurger.addEventListener('click', () => {
    navbarBurger.classList.toggle('is-active');
    burgerTarget.classList.toggle('is-active');
  });
  main.addEventListener('click', () => {
    burgerTarget.classList.remove('is-active');
  });

  const textArea = document.querySelector('.sample-text');
  const regularBtn = document.getElementById('regular');
  regularBtn.addEventListener('input', () => {
    textArea.style.fontWeight = 400;
  });
  const boldBtn = document.getElementById('bold');
  boldBtn.addEventListener('input', () => {
    textArea.style.fontWeight = 700;
  });
  const weightSldr = document.getElementById('weight');
  weightSldr.value = parseInt(window.getComputedStyle(textArea)['fontSize']);
  weightSldr.addEventListener('input', () => {
    textArea.style.fontSize = weightSldr.value + 'px';
  });
});