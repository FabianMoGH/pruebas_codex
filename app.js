const personas = [];

const form = document.querySelector("#person-form");
const nameInput = document.querySelector("#name");
const aliasInput = document.querySelector("#alias");
const paidInput = document.querySelector("#paid");
const payerInput = document.querySelector("#payer");
const minorInput = document.querySelector("#minor");
const payerOptions = document.querySelector("#payer-options");
const peopleBody = document.querySelector("#people-body");
const message = document.querySelector("#message");
const result = document.querySelector("#result");
const calculateButton = document.querySelector("#calculate-button");
const clearButton = document.querySelector("#clear-button");

function formatearImporte(importe) {
  const texto = importe.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return texto.replaceAll(",", "X").replaceAll(".", ",").replaceAll("X", ".");
}

function parsearImporte(texto) {
  let valor = texto.trim().replaceAll(" ", "");

  if (!valor) {
    return 0;
  }

  if (valor.includes(",")) {
    valor = valor.replaceAll(".", "").replaceAll(",", ".");
  } else if (valor.includes(".")) {
    const partes = valor.split(".");
    if (partes.length > 1 && partes.at(-1).length === 3) {
      valor = valor.replaceAll(".", "");
    }
  }

  const numero = Number(valor);

  if (!Number.isFinite(numero)) {
    throw new Error("Importe invalido");
  }

  return numero;
}

function calcularTransferencias(listaPersonas) {
  const total = listaPersonas.reduce((suma, persona) => suma + persona.importePagado, 0);
  const totalPesos = listaPersonas.reduce((suma, persona) => suma + (persona.menor ? 0.5 : 1), 0);

  if (totalPesos === 0) {
    return {
      total: 0,
      valorAdulto: 0,
      saldos: [],
      saldosPagadores: [],
      transferencias: [],
    };
  }

  const valorAdulto = total / totalPesos;
  const saldos = [];
  const saldosPorPagador = new Map();

  listaPersonas.forEach((persona, indice) => {
    const peso = persona.menor ? 0.5 : 1;
    const debePagar = valorAdulto * peso;
    const saldo = redondear(persona.importePagado - debePagar);
    const pagador = persona.pagador || persona.nombre;

    saldos.push({ indice, saldo });
    saldosPorPagador.set(pagador, redondear((saldosPorPagador.get(pagador) || 0) + saldo));
  });

  const deudores = [];
  const acreedores = [];

  saldosPorPagador.forEach((saldo, pagador) => {
    if (saldo < 0) {
      deudores.push([pagador, -saldo]);
    } else if (saldo > 0) {
      acreedores.push([pagador, saldo]);
    }
  });

  const transferencias = [];
  let i = 0;
  let j = 0;

  while (i < deudores.length && j < acreedores.length) {
    const [deudorPagador, debe] = deudores[i];
    const [acreedorPagador, cobra] = acreedores[j];
    const monto = Math.min(debe, cobra);

    transferencias.push([deudorPagador, acreedorPagador, redondear(monto)]);

    deudores[i][1] -= monto;
    acreedores[j][1] -= monto;

    if (deudores[i][1] < 0.01) {
      i += 1;
    }

    if (acreedores[j][1] < 0.01) {
      j += 1;
    }
  }

  const saldosPagadores = Array.from(saldosPorPagador, ([pagador, saldo]) => ({ pagador, saldo }));

  return { total, valorAdulto, saldos, saldosPagadores, transferencias };
}

function redondear(numero) {
  return Math.round((numero + Number.EPSILON) * 100) / 100;
}

function agregarPersona(event) {
  event.preventDefault();
  limpiarMensaje();

  const nombre = nameInput.value.trim();
  const alias = aliasInput.value.trim();
  const pagadoTexto = paidInput.value.trim();
  const pagador = payerInput.value.trim() || nombre;
  const nombresCargados = personas.map((persona) => persona.nombre);

  if (!nombre) {
    mostrarMensaje("Ingresa el nombre de la persona.");
    return;
  }

  if (nombresCargados.includes(nombre)) {
    mostrarMensaje("Ya existe una persona con ese nombre.");
    return;
  }

  let pagado;

  try {
    pagado = parsearImporte(pagadoTexto);
  } catch (_error) {
    mostrarMensaje("Ingresa un importe válido.");
    return;
  }

  if (pagado < 0) {
    mostrarMensaje("El importe no puede ser negativo.");
    return;
  }

  if (pagado > 0 && !alias) {
    mostrarMensaje("Ingresa el alias de pago de la persona.");
    return;
  }

  if (pagador !== nombre && !nombresCargados.includes(pagador)) {
    mostrarMensaje("El pagador debe estar cargado en la lista o quedar vacío.");
    return;
  }

  personas.push({
    nombre,
    alias,
    menor: minorInput.checked,
    importePagado: pagado,
    pagador,
  });

  form.reset();
  paidInput.value = "0.00";
  renderizarPersonas();
  actualizarPagadores();
  actualizarEstadoCalculo();
  nameInput.focus();
}

function quitarPersona(indice) {
  personas.splice(indice, 1);
  repararPagadoresEliminados();
  renderizarPersonas();
  actualizarPagadores();
  actualizarEstadoCalculo();
}

function limpiarPersonas() {
  personas.splice(0, personas.length);
  result.innerHTML = "";
  payerInput.value = "";
  limpiarMensaje();
  renderizarPersonas();
  actualizarPagadores();
  actualizarEstadoCalculo();
}

function calcular() {
  limpiarMensaje();

  if (!personas.length) {
    mostrarMensaje("Agrega al menos una persona para calcular.");
    return;
  }

  const { total, valorAdulto, saldos, saldosPagadores, transferencias } = calcularTransferencias(personas);
  const personasPorNombre = new Map(personas.map((persona) => [persona.nombre, persona]));
  const saldosPorIndice = new Map(saldos.map((saldoPersona) => [saldoPersona.indice, saldoPersona.saldo]));
  const lineas = [
    [`TOTAL GASTADO: ${formatearImporte(total)}`, false],
    [`VALOR ADULTO: ${formatearImporte(valorAdulto)}`, false],
    [`VALOR MENOR: ${formatearImporte(valorAdulto * 0.5)}`, true],
    ["", false],
    ["SALDOS:", false],
  ];

  saldosPagadores.forEach((saldoPagador) => {
    const { pagador, saldo } = saldoPagador;
    const personaPagadora = personasPorNombre.get(pagador);
    const esMenor = Boolean(personaPagadora && personaPagadora.menor);
    const alias = aliasVisible(personaPagadora);

    lineas.push([lineaSaldo(pagador, alias, saldo), esMenor]);

    personas.forEach((persona, indice) => {
      if (persona.pagador !== pagador || persona.nombre === pagador) {
        return;
      }

      const saldoIndividual = saldosPorIndice.get(indice);
      const aliasIndividual = aliasVisible(persona);
      const linea = lineaSaldo(
        persona.nombre,
        aliasIndividual,
        saldoIndividual,
        "\t",
        ` - paga ${pagador}`,
      );

      lineas.push([linea, persona.menor]);
    });

    lineas.push(["", false]);
  });

  lineas.push(["TRANSFERENCIAS ENTRE PAGADORES:", false]);

  if (!transferencias.length) {
    lineas.push(["No hace falta transferir nada.", false]);
  } else {
    transferencias.forEach(([deudorPagador, acreedorPagador, monto]) => {
      const deudor = personasPorNombre.get(deudorPagador);
      const acreedor = personasPorNombre.get(acreedorPagador);
      const aliasAcreedor = aliasVisible(acreedor);
      const esMenor = Boolean((deudor && deudor.menor) || (acreedor && acreedor.menor));

      lineas.push([
        `${deudorPagador} transfiere ${formatearImporte(monto)} a ${acreedorPagador} (alias: ${aliasAcreedor})`,
        esMenor,
      ]);
    });
  }

  mostrarResultado(lineas);
}

function renderizarPersonas() {
  peopleBody.innerHTML = "";

  if (!personas.length) {
    const row = document.createElement("tr");
    row.className = "empty-row";
    row.innerHTML = '<td colspan="6">No hay personas cargadas.</td>';
    peopleBody.append(row);
    return;
  }

  personas.forEach((persona, indice) => {
    const row = document.createElement("tr");

    if (persona.menor) {
      row.classList.add("minor-row");
    }

    row.innerHTML = `
      <td></td>
      <td></td>
      <td>${persona.menor ? "Menor" : "Adulto"}</td>
      <td></td>
      <td class="number">${formatearImporte(persona.importePagado)}</td>
      <td><button type="button" class="remove" data-index="${indice}">Quitar</button></td>
    `;

    row.children[0].textContent = persona.nombre;
    row.children[1].textContent = aliasVisible(persona);
    row.children[3].textContent = persona.pagador;
    peopleBody.append(row);
  });
}

function mostrarResultado(lineas) {
  result.innerHTML = "";

  lineas.forEach(([texto, esMenor]) => {
    const span = document.createElement("span");
    span.textContent = `${texto}\n`;

    if (esMenor) {
      span.className = "minor";
    }

    result.append(span);
  });
}

function actualizarPagadores() {
  payerOptions.innerHTML = "";

  personas.forEach((persona) => {
    const option = document.createElement("option");
    option.value = persona.nombre;
    payerOptions.append(option);
  });
}

function actualizarEstadoCalculo() {
  calculateButton.disabled = personas.length === 0;
}

function repararPagadoresEliminados() {
  const nombres = new Set(personas.map((persona) => persona.nombre));

  personas.forEach((persona) => {
    if (!nombres.has(persona.pagador)) {
      persona.pagador = persona.nombre;
    }
  });
}

function aliasVisible(persona) {
  if (!persona) {
    return "x";
  }

  return persona.alias || "x";
}

function lineaSaldo(nombre, alias, saldo, prefijo = "", sufijo = "") {
  const persona = `${nombre} (${alias})`;
  let textoSaldo = "está hecho";

  if (saldo > 0) {
    textoSaldo = `debe cobrar ${formatearImporte(saldo)}`;
  } else if (saldo < 0) {
    textoSaldo = `debe pagar ${formatearImporte(-saldo)}`;
  }

  return `${prefijo}${persona} ${textoSaldo}${sufijo}`;
}

function mostrarMensaje(texto) {
  message.textContent = texto;
}

function limpiarMensaje() {
  message.textContent = "";
}

form.addEventListener("submit", agregarPersona);
clearButton.addEventListener("click", limpiarPersonas);
calculateButton.addEventListener("click", calcular);

peopleBody.addEventListener("click", (event) => {
  const button = event.target.closest(".remove");

  if (!button) {
    return;
  }

  quitarPersona(Number(button.dataset.index));
});
