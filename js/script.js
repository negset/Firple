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
  const weight = document.getElementById("weight");
  const weightText = document.getElementById("weight-text");
  weight.value = parseInt(window.getComputedStyle(textArea)["fontSize"]);
  weightText.innerHTML = window.getComputedStyle(textArea)["fontSize"];
  weight.oninput = e => {
    textArea.style.fontSize = e.target.value + "px";
    weightText.innerHTML = e.target.value + "px";
  };
  document.getElementById("bold").oninput = e => {
    textArea.style.fontWeight = e.target.checked ? 700 : 400;
  };
  document.getElementById("italic").oninput = e => {
    textArea.style.fontStyle = e.target.checked ? "italic" : "normal";
  };
  document.getElementById("ligature").oninput = e => {
    textArea.style.fontVariantLigatures = e.target.checked ? "normal" : "none";
  };
  const cv33 = document.getElementById("cv33");
  const ss11 = document.getElementById("ss11");
  featureOnInput = e => {
    if (cv33.checked && ss11.checked)
      textArea.style.fontFeatureSettings = "'cv33', 'ss11'";
    else if (cv33.checked)
      textArea.style.fontFeatureSettings = "'cv33'";
    else if (ss11.checked)
      textArea.style.fontFeatureSettings = "'ss11'";
    else
      textArea.style.fontFeatureSettings = "";
  };
  cv33.oninput = featureOnInput;
  ss11.oninput = featureOnInput;
});