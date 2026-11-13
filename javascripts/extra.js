/* Local navigation: keep every address relative to this manual folder. */
document.addEventListener("DOMContentLoaded", function () {
  const title = document.querySelector(".md-header__title");
  if (!title) return;
  const home = document.createElement("a");
  home.className = "custom-header-home";
  home.href = "index.html";
  home.textContent = "HOME";
  const separator = document.createElement("span");
  separator.className = "custom-header-separator";
  separator.textContent = "|";
  const label = document.createElement("span");
  label.className = "custom-header-title";
  label.textContent = "CEREBRO AI MANUAL";
  title.replaceChildren(home, separator, label);
});
