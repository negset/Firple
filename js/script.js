document.addEventListener("DOMContentLoaded", () => {
  const main = document.querySelector("main");
  const navHeight = window.getComputedStyle(document.querySelector("nav"))["height"];
  const footerHeight = window.getComputedStyle(document.querySelector("footer"))["height"];
  main.style.minHeight = `calc(100vh - ${navHeight} - ${footerHeight})`;

  const navbarBurger = document.querySelector(".navbar-burger");
  const burgerTarget = document.getElementById(navbarBurger.dataset.target);
  navbarBurger.onclick = () => {
    navbarBurger.classList.toggle("is-active");
    burgerTarget.classList.toggle("is-active");
  };
  main.onclick = () => {
    navbarBurger.classList.remove("is-active");
    burgerTarget.classList.remove("is-active");
  };

  const textArea = document.querySelector(".sample-text");
  document.getElementById("subfamily").onchange = e => {
    const v = e.target.value;
    textArea.style.fontFamily = (v == "firple") ? "Firple" : "Firple Slim";
  };
  document.getElementById("bold").oninput = e => {
    textArea.style.fontWeight = e.target.checked ? 700 : 400;
  };
  document.getElementById("italic").oninput = e => {
    textArea.style.fontStyle = e.target.checked ? "italic" : "normal";
  };
  const weight = document.getElementById("weight");
  weight.value = parseInt(window.getComputedStyle(textArea)["fontSize"]);
  weight.oninput = e => {
    textArea.style.fontSize = e.target.value + "px";
  };
  document.getElementById("ligature").oninput = e => {
    textArea.style.fontVariantLigatures = e.target.checked ? "normal" : "none";
  };
});