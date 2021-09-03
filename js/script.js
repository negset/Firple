document.addEventListener('DOMContentLoaded', () => {
  const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
  if ($navbarBurgers.length > 0) {
    $navbarBurgers.forEach(el => {
      el.addEventListener('click', () => {
        const target = el.dataset.target;
        const $target = document.getElementById(target);
        el.classList.toggle('is-active');
        $target.classList.toggle('is-active');
      });
    });
  }

  const textArea = document.getElementById('sample-text');
  const regularBtn = document.getElementById('regular');
  regularBtn.addEventListener('input', () => {
    textArea.style.fontWeight = 400;
  });
  const boldBtn = document.getElementById('bold');
  boldBtn.addEventListener('input', () => {
    textArea.style.fontWeight = 700;
  });
  const weightSldr = document.getElementById('weight');
  weightSldr.addEventListener('input', () => {
    textArea.style.fontSize = weightSldr.value + "%";
  });
});