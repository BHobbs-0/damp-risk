// Observable Framework config: https://observablehq.com/framework/config
// Data loaders (src/data/*.py) run with the project's Python virtual environment,
// so the analysis stays in Python and the dashboard only reads small JSON files.
const python = process.platform === "win32" ? "../.venv/Scripts/python.exe" : "../.venv/bin/python";

export default {
  title: "Damp Risk Atlas",
  root: "src",
  style: "style.css", // our own design replaces Framework's default theme
  sidebar: false, // we draw our own icon rail
  toc: false,
  pager: false,
  header: "",
  footer: "",
  interpreters: {".py": [python]},
  head: '<link rel="icon" href="data:,">'
};
