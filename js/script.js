document.addEventListener("DOMContentLoaded", () => {
  // main min-height
  const main = document.querySelector("main");
  const navHeight = getComputedStyle(document.querySelector("nav"))["height"];
  const footerHeight = getComputedStyle(document.querySelector("footer"))["height"];
  main.style.minHeight = `calc(100vh - ${navHeight} - ${footerHeight})`;

  // navbar burger
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

  // preview config
  const previewConfig = document.querySelector("#preview-config");
  const textArea = document.querySelector("#preview-text");
  document.querySelector("#subfamily").onchange = e => {
    const v = e.target.value;
    textArea.style.fontFamily = (v == "firple") ? "Firple" : "Firple Slim";
  };
  const boldButton = document.querySelector("#bold-button");
  boldButton.onclick = () => {
    let active = boldButton.classList.toggle("is-active");
    textArea.style.fontWeight = active ? 700 : 400;
  };
  const italicButton = document.querySelector("#italic-button");
  italicButton.onclick = () => {
    let active = italicButton.classList.toggle("is-active");
    textArea.style.fontStyle = active ? "italic" : "normal";
  };
  const weightSlider = document.querySelector("#weight-slider");
  const weightText = document.querySelector("#weight-text");
  weightSlider.value = parseInt(getComputedStyle(textArea)["fontSize"]);
  weightText.innerHTML = getComputedStyle(textArea)["fontSize"];
  weightSlider.oninput = e => {
    textArea.style.fontSize = e.target.value + "px";
    weightText.innerHTML = e.target.value + "px";
  };
  document.querySelector("#ligature-checkbox").oninput = e => {
    textArea.style.fontVariantLigatures = e.target.checked ? "normal" : "none";
  };
  // features
  const features = {
    cv33: false,
    ss11: false,
  };
  function toggleFeature(tag) {
    features[tag] = !features[tag];
    textArea.style.fontFeatureSettings = Object.entries(features)
      .map(([tag, enabled]) => `"${tag}" ${enabled ? 1 : 0}`)
      .join(", ");
  }
  document.querySelectorAll(".feature-checkbox").forEach(e => {
    e.oninput = () => toggleFeature(e.dataset.tag);
  });

  // font loading
  document.fonts.ready.then(() => {
    previewConfig.disabled = false;
    textArea.value =
      `彼らの機器や装置はすべて生命体だ。
Almost before we knew it, we had left the ground.

!=->>++:=`
  });
  document.fonts.onloading = () => {
    previewConfig.disabled = true;
    let currentText = textArea.value;
    textArea.value = "読み込み中...";

    document.fonts.onloadingdone = () => {
      previewConfig.disabled = false;
      textArea.value = currentText;
    };
  };
});
