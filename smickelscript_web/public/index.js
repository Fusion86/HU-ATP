const exampleCodeSelect = document.getElementById("select-example-code");
const sourceCodeArea = document.getElementById("input-textarea");

const isDev = document.location.host.indexOf("localhost") != -1;
const apiUrl = isDev ? "http://localhost:5000" : "https://saas.cerbus.nl/api";

async function compileCode() {
  const status = document.getElementById("status-text");
  const dst = document.getElementById("arm-code-field");

  const res = await fetch(apiUrl + "/compile", {
    method: "POST",
    body: sourceCodeArea.value,
  });

  const data = await res.json();

  if (data.message == "Ok") {
    dst.textContent = data.asm;
    dst.style.display = "block";
    status.style.display = "none";
  } else {
    status.innerHTML = data.message;
    dst.style.display = "none";
    status.style.display = "block";
  }
}

function exampleCodeSelectionChanged() {
  sourceCodeArea.value = exampleCodeSelect.value;
}

async function loadExampleCode() {
  const res = await fetch("examples.json");

  if (res.ok) {
    const examples = await res.json();
    console.dir(examples);

    for (const example of examples) {
      const opt = document.createElement("option");
      opt.value = example[1];
      opt.innerHTML = example[0];
      exampleCodeSelect.appendChild(opt);
    }
  }
}

loadExampleCode();
