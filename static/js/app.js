// ── Utils ────────────────────────────────────────────────────────────────
function $(id) { return document.getElementById(id); }
function val(id) { return $(id) ? $(id).value.trim() : ""; }
function checked(id) { return $(id) ? $(id).checked : false; }

function showToast(msg, error = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "toast" + (error ? " error" : "");
  t.style.display = "block";
  setTimeout(() => t.style.display = "none", 3000);
}

function showView(name) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
  $("view-" + name).classList.add("active");
  document.querySelectorAll(".tab")[name === "form" ? 0 : 1].classList.add("active");
  if (name === "history") carregarHistorico();
  if (name === "form" && !modoEdicaoId) {
    limparFormulario();
    preencherComUltimoRegisto();
  }
}

// ── Km percorridos auto-calcula ──────────────────────────────────────────
$("km_inicio").addEventListener("input", calcKm);
$("km_fim").addEventListener("input", calcKm);
function calcKm() {
  const ini = parseInt(val("km_inicio")) || 0;
  const fim = parseInt(val("km_fim")) || 0;
  if (ini && fim && fim > ini) $("km_percorridos").value = fim - ini;
}

// ── Pré-preencher com dados do último registo ─────────────────────────────
async function preencherComUltimoRegisto() {
  $("data").value = new Date().toISOString().split("T")[0];

  // Horas do dia ficam sempre em branco
  ["hora_entrada","hora_almoco","hora_saida","horas_extras",
   "hora_ligou","hora_desligou","horas_motor_desligou"].forEach(id => {
    if ($(id)) $(id).value = "";
  });

  try {
    const res = await fetch("/api/registos");
    const lista = await res.json();
    if (!lista.length) return;

    const ultimo = await fetch(`/api/registos/${lista[0].id}`).then(r => r.json());

    // Identificação — igual ao último
    ["central","carro_n","marca","matricula","empresa","motorista_nome","responsavel"].forEach(id => {
      if ($(id) && ultimo[id]) $(id).value = ultimo[id];
    });

    // Nº folha incrementa 1
    if (ultimo.numero) $("numero").value = (parseInt(ultimo.numero) || 0) + 1;

    // Km iniciais = km finais do último registo
    if (ultimo.km_fim) {
      $("km_inicio").value = ultimo.km_fim;
      $("km_fim").value = "";
      $("km_percorridos").value = "";
    }

    // Horas motor iniciais = horas motor finais do último registo
    if (ultimo.horas_finais_motor) $("horas_iniciais_motor").value = ultimo.horas_finais_motor;
    if (ultimo.horas_finais_bomba) $("horas_iniciais_bomba").value = ultimo.horas_finais_bomba;
    $("horas_finais_motor").value = "";
    $("horas_finais_bomba").value = "";

  } catch (e) {
    // se falhar não faz nada
  }
}

preencherComUltimoRegisto();

// ── OBRAS ────────────────────────────────────────────────────────────────
let obraId = 0;
const isMobile = () => window.innerWidth <= 700;

function addObra(dados = {}) {
  obraId++;
  const id = obraId;

  // ── Desktop: linha na tabela ──
  const tr = document.createElement("tr");
  tr.id = "obra-" + id;
  tr.innerHTML = `
    <td><input type="text" value="${dados.cliente||''}" placeholder="Cliente" style="min-width:100px"></td>
    <td><input type="text" value="${dados.guia||''}" placeholder="Nº guia" style="min-width:80px"></td>
    <td><input type="text" value="${dados.designacao||''}" placeholder="Designação" style="min-width:90px"></td>
    <td style="text-align:center"><input type="checkbox" ${dados.bombeado?'checked':''} title="Bombeado"></td>
    <td style="text-align:center"><input type="checkbox" ${dados.directo?'checked':''} title="Directo"></td>
    <td><input type="number" value="${dados.m3||''}" placeholder="0.0" step="0.5" style="min-width:50px" oninput="updateTotal()"></td>
    <td><input type="text" value="${dados.mangueiras||''}" placeholder="—" style="min-width:60px"></td>
    <td><input type="time" value="${dados.hora_saida_central||''}"></td>
    <td><input type="text" value="${dados.local_descarga||''}" placeholder="Local" style="min-width:100px"></td>
    <td><input type="time" value="${dados.hora_chegada_obra||''}"></td>
    <td><input type="time" value="${dados.inicio_descarga||''}"></td>
    <td><input type="time" value="${dados.fim_descarga||''}"></td>
    <td><input type="time" value="${dados.hora_saida_obra||''}"></td>
    <td><input type="time" value="${dados.hora_chegada_central||''}"></td>
    <td><button class="btn-danger" onclick="removeObra(${id})" title="Remover">×</button></td>
  `;
  $("obras-body").appendChild(tr);

  // ── Mobile: cartão ──
  const bombeadoActive = dados.bombeado ? "active" : "";
  const directoActive  = dados.directo  ? "active" : "";
  const card = document.createElement("div");
  card.className = "obra-card";
  card.id = "obra-card-" + id;
  const num = $("obras-body").children.length;
  card.innerHTML = `
    <div class="obra-card-header">
      <span class="obra-card-num">Obra ${num}</span>
      <button class="btn-danger" onclick="removeObra(${id})">×</button>
    </div>
    <div class="grid g2">
      <div class="field"><label>Cliente <span class="req">*</span></label>
        <input type="text" value="${dados.cliente||''}" placeholder="Nome do cliente" oninput="syncDesktop(${id},0,this.value)"></div>
      <div class="field"><label>Guia Remessa <span class="req">*</span></label>
        <input type="text" value="${dados.guia||''}" placeholder="Nº guia" oninput="syncDesktop(${id},1,this.value)"></div>
    </div>
    <div class="field" style="margin-top:8px"><label>Designação</label>
      <input type="text" value="${dados.designacao||''}" placeholder="ex: Betão C25/30" oninput="syncDesktop(${id},2,this.value)"></div>
    <div style="margin-top:10px">
      <p class="sublabel">Tipo <span class="req">*</span></p>
      <div class="tipo-toggle">
        <button type="button" class="tipo-btn ${directoActive}"  id="tipo-directo-${id}"  onclick="setTipo(${id},'directo')">Directo</button>
        <button type="button" class="tipo-btn ${bombeadoActive}" id="tipo-bombeado-${id}" onclick="setTipo(${id},'bombeado')">Bombeado</button>
      </div>
    </div>
    <div class="grid g2" style="margin-top:8px">
      <div class="field"><label>Quant. m³ <span class="req">*</span></label>
        <input type="number" value="${dados.m3||''}" placeholder="0.0" step="0.5" oninput="syncDesktop(${id},5,this.value);updateTotal()"></div>
      <div class="field"><label>Mangueiras / Linha Tubos</label>
        <input type="text" value="${dados.mangueiras||''}" placeholder="—" oninput="syncDesktop(${id},6,this.value)"></div>
    </div>
    <div class="grid g2" style="margin-top:8px">
      <div class="field"><label>Hora Saída Central <span class="req">*</span></label>
        <input type="time" value="${dados.hora_saida_central||''}" oninput="syncDesktop(${id},7,this.value)"></div>
      <div class="field"><label>Hora Chegada à Obra <span class="req">*</span></label>
        <input type="time" value="${dados.hora_chegada_obra||''}" oninput="syncDesktop(${id},9,this.value)"></div>
    </div>
    <div class="field" style="margin-top:8px"><label>Local da Descarga <span class="req">*</span></label>
      <input type="text" value="${dados.local_descarga||''}" placeholder="Morada / local" oninput="syncDesktop(${id},8,this.value)"></div>
    <div class="grid g2" style="margin-top:8px">
      <div class="field"><label>Início Descarga <span class="req">*</span></label>
        <input type="time" value="${dados.inicio_descarga||''}" oninput="syncDesktop(${id},10,this.value)"></div>
      <div class="field"><label>Fim Descarga <span class="req">*</span></label>
        <input type="time" value="${dados.fim_descarga||''}" oninput="syncDesktop(${id},11,this.value)"></div>
    </div>
    <div class="grid g2" style="margin-top:8px">
      <div class="field"><label>Hora Saída da Obra <span class="req">*</span></label>
        <input type="time" value="${dados.hora_saida_obra||''}" oninput="syncDesktop(${id},12,this.value)"></div>
      <div class="field"><label>Hora Chegada Central</label>
        <input type="time" value="${dados.hora_chegada_central||''}" oninput="syncDesktop(${id},13,this.value)"></div>
    </div>
  `;
  $("obras-cards-mobile").appendChild(card);
  aplicarMascarasCartao(card);

  updateTotal();
  updateMobileVisibility();
}

function setTipo(id, tipo) {
  const tr = $("obra-" + id);
  if (!tr) return;
  const inputs = tr.querySelectorAll("input");
  // checkboxes: index 3 = bombeado, 4 = directo
  inputs[3].checked = (tipo === "bombeado");
  inputs[4].checked = (tipo === "directo");

  $("tipo-bombeado-" + id).classList.toggle("active", tipo === "bombeado");
  $("tipo-directo-"  + id).classList.toggle("active", tipo === "directo");
}

function syncDesktop(id, inputIndex, value) {
  const tr = $("obra-" + id);
  if (!tr) return;
  const inputs = tr.querySelectorAll("input");
  if (inputs[inputIndex]) inputs[inputIndex].value = value;
}

function updateMobileVisibility() {
  const mobile = isMobile();
  const cards = $("obras-cards-mobile");
  if (cards) cards.style.display = mobile ? "block" : "none";
}

window.addEventListener("resize", updateMobileVisibility);
updateMobileVisibility();

function removeObra(id) {
  [$("obra-" + id), $("obra-card-" + id)].forEach(el => { if (el) el.remove(); });
  updateTotal();
  // renumera cartões
  document.querySelectorAll(".obra-card-num").forEach((el, i) => el.textContent = `Obra ${i+1}`);
}

function updateTotal() {
  let total = 0;
  $("obras-body").querySelectorAll("tr").forEach(tr => {
    const m3Input = tr.querySelectorAll("input")[5];
    total += parseFloat(m3Input?.value || 0);
  });
  $("total-m3").textContent = "Total: " + total.toFixed(1) + " m³";
}

function getObras() {
  return Array.from($("obras-body").querySelectorAll("tr")).map(tr => {
    const inputs = tr.querySelectorAll("input");
    return {
      cliente:             inputs[0].value,
      guia:                inputs[1].value,
      designacao:          inputs[2].value,
      bombeado:            inputs[3].checked ? "X" : "",
      directo:             inputs[4].checked ? "X" : "",
      m3:                  inputs[5].value,
      mangueiras:          inputs[6].value,
      hora_saida_central:  inputs[7].value,
      local_descarga:      inputs[8].value,
      hora_chegada_obra:   inputs[9].value,
      inicio_descarga:     inputs[10].value,
      fim_descarga:        inputs[11].value,
      hora_saida_obra:     inputs[12].value,
      hora_chegada_central:inputs[13].value,
    };
  });
}

// ── GASÓLEO ──────────────────────────────────────────────────────────────
let gasId = 0;

function addGasoleo(dados = {}) {
  gasId++;
  const id = gasId;
  const tr = document.createElement("tr");
  tr.id = "gas-" + id;
  tr.innerHTML = `
    <td><input type="text" value="${dados.fornecedor||''}" placeholder="Fornecedor" style="min-width:120px"></td>
    <td><input type="text" value="${dados.req_n||''}" placeholder="Nº" style="min-width:60px"></td>
    <td><input type="number" value="${dados.litros||''}" placeholder="0" style="min-width:60px"></td>
    <td><input type="time" value="${dados.hora||''}"></td>
    <td><input type="text" value="${dados.designacao||''}" placeholder="Gasóleo/Óleo..." style="min-width:100px"></td>
    <td><button class="btn-danger" onclick="removeGas(${id})" title="Remover">×</button></td>
  `;
  $("gasoleo-body").appendChild(tr);
}

function removeGas(id) {
  const el = $("gas-" + id);
  if (el) el.remove();
}

function getGasoleo() {
  return Array.from($("gasoleo-body").querySelectorAll("tr")).map(tr => {
    const inputs = tr.querySelectorAll("input");
    return {
      fornecedor:  inputs[0].value,
      req_n:       inputs[1].value,
      litros:      inputs[2].value,
      hora:        inputs[3].value,
      designacao:  inputs[4].value,
    };
  });
}

// ── VALIDAÇÃO ────────────────────────────────────────────────────────────
function parseHora(s) {
  // aceita "HH:MM" e devolve minutos totais, ou null se inválido
  if (!s) return null;
  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  return parseInt(m[1]) * 60 + parseInt(m[2]);
}

function validar() {
  const erros = [];

  // Campos simples obrigatórios
  const obrigatorios = [
    ["data",         "Data"],
    ["carro_n",      "Carro N.º"],
    ["matricula",    "Matrícula"],
    ["hora_entrada", "Hora de Entrada"],
    ["hora_almoco",  "Hora de Almoço"],
    ["hora_saida",   "Hora de Saída"],
    ["km_inicio",    "Km Início"],
    ["km_fim",       "Km Fim"],
  ];

  obrigatorios.forEach(([id, nome]) => {
    const el = $(id);
    if (!el) return;
    if (!el.value.trim()) {
      erros.push(nome);
      el.classList.add("invalid");
    } else {
      el.classList.remove("invalid");
    }
  });

  // ── Km finais não podem ser menores que os iniciais ──
  const kmIni = parseInt(val("km_inicio")) || 0;
  const kmFim = parseInt(val("km_fim")) || 0;
  if (kmIni && kmFim && kmFim < kmIni) {
    erros.push("Km Fim não pode ser menor que Km Início");
    $("km_fim").classList.add("invalid");
  }

  // ── Horas do dia: saída >= entrada, almoço entre entrada e saída ──
  const hEnt  = parseHora(val("hora_entrada"));
  const hAlm  = parseHora(val("hora_almoco"));
  const hSai  = parseHora(val("hora_saida"));
  if (hEnt !== null && hSai !== null && hSai < hEnt) {
    erros.push("Hora de Saída não pode ser anterior à Hora de Entrada");
    $("hora_saida").classList.add("invalid");
  }
  if (hEnt !== null && hAlm !== null && hAlm < hEnt) {
    erros.push("Hora de Almoço não pode ser anterior à Hora de Entrada");
    $("hora_almoco").classList.add("invalid");
  }

  // ── Horas Motor: finais >= iniciais ──
  const hmIni = parseFloat(val("horas_iniciais_motor")) || 0;
  const hmFim = parseFloat(val("horas_finais_motor"))   || 0;
  if (hmIni && hmFim && hmFim < hmIni) {
    erros.push("Horas Finais Motor não podem ser menores que as Iniciais");
    $("horas_finais_motor").classList.add("invalid");
  }
  const hbIni = parseFloat(val("horas_iniciais_bomba")) || 0;
  const hbFim = parseFloat(val("horas_finais_bomba"))   || 0;
  if (hbIni && hbFim && hbFim < hbIni) {
    erros.push("Horas Finais Bomba não podem ser menores que as Iniciais");
    $("horas_finais_bomba").classList.add("invalid");
  }

  // Validação das obras
  const linhas = $("obras-body").querySelectorAll("tr");
  linhas.forEach((tr, i) => {
    const inputs = tr.querySelectorAll("input");
    const temDados = Array.from(inputs).some(inp => inp.type !== "checkbox" && inp.value.trim());
    if (!temDados) return; // linha vazia, ignora

    const camposObra = [
      [0, "Cliente"],
      [1, "Guia Remessa"],
      [5, "Quant. m³"],
      [7, "Hora Saída Central"],
      [8, "Local Descarga"],
      [9, "Hora Chegada Obra"],
      [10, "Início Descarga"],
      [11, "Fim Descarga"],
      [12, "Hora Saída Obra"],
    ];

    // Bombeado ou Directo — pelo menos um
    const bombeado = inputs[3].checked;
    const directo  = inputs[4].checked;
    if (!bombeado && !directo) {
      erros.push(`Obra ${i+1}: Bombeado ou Directo`);
      inputs[3].closest("td").style.background = "#fff5f5";
      inputs[4].closest("td").style.background = "#fff5f5";
    } else {
      inputs[3].closest("td").style.background = "";
      inputs[4].closest("td").style.background = "";
    }

    camposObra.forEach(([idx, nome]) => {
      if (!inputs[idx].value.trim()) {
        erros.push(`Obra ${i+1}: ${nome}`);
        inputs[idx].classList.add("invalid");
      } else {
        inputs[idx].classList.remove("invalid");
      }
    });
  });

  return erros;
}

// ── GUARDAR ──────────────────────────────────────────────────────────────
async function guardarRegisto() {
  const erros = validar();
  if (erros.length) {
    showToast("Preenche os campos obrigatórios: " + erros.slice(0, 3).join(", ") + (erros.length > 3 ? "..." : ""), true);
    return;
  }

  const dados = {
    data:                 val("data"),
    central:              val("central"),
    carro_n:              val("carro_n"),
    marca:                val("marca"),
    matricula:            val("matricula"),
    empresa:              val("empresa"),
    numero:               val("numero"),
    hora_entrada:         val("hora_entrada"),
    hora_almoco:          val("hora_almoco"),
    hora_saida:           val("hora_saida"),
    horas_extras:         val("horas_extras"),
    km_inicio:            val("km_inicio"),
    km_fim:               val("km_fim"),
    km_percorridos:       val("km_percorridos"),
    horas_iniciais_motor: val("horas_iniciais_motor"),
    horas_finais_motor:   val("horas_finais_motor"),
    horas_iniciais_bomba: val("horas_iniciais_bomba"),
    horas_finais_bomba:   val("horas_finais_bomba"),
    hora_ligou:           val("hora_ligou"),
    hora_desligou:        val("hora_desligou"),
    horas_motor_desligou: val("horas_motor_desligou"),
    motorista_nome:       val("motorista_nome"),
    responsavel:          val("responsavel"),
    viatura_limpa_int:    checked("viatura_limpa_int") ? 1 : 0,
    viatura_limpa_ext:    checked("viatura_limpa_ext") ? 1 : 0,
    viatura_lubrificada:  checked("viatura_lubrificada") ? 1 : 0,
    oleo_motor_ok:        checked("oleo_motor_ok") ? 1 : 0,
    oleo_motor_naook:     checked("oleo_motor_naook") ? 1 : 0,
    oleo_motor_notas:     val("oleo_motor_notas"),
    oleo_sis_ok:          checked("oleo_sis_ok") ? 1 : 0,
    oleo_sis_naook:       checked("oleo_sis_naook") ? 1 : 0,
    oleo_sis_notas:       val("oleo_sis_notas"),
    agua_rad_ok:          checked("agua_rad_ok") ? 1 : 0,
    agua_rad_naook:       checked("agua_rad_naook") ? 1 : 0,
    agua_rad_notas:       val("agua_rad_notas"),
    observacoes:          val("observacoes"),
    obras:                getObras(),
    gasoleo:              getGasoleo(),
  };

  try {
    const url    = modoEdicaoId ? `/api/registos/${modoEdicaoId}` : "/api/registos";
    const method = modoEdicaoId ? "PUT" : "POST";
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const json = await res.json();
    if (res.ok) {
      if (modoEdicaoId) {
        showToast("✓ Registo atualizado! (Folha nº" + dados.numero + ")");
        cancelarEdicao();
      } else {
        showToast("✓ Registo guardado! (Folha nº" + dados.numero + ")");
        const nAtual = parseInt(val("numero")) || 0;
        $("numero").value = nAtual + 1;
      }
    } else {
      showToast("Erro ao guardar: " + (json.erro || "erro desconhecido"), true);
    }
  } catch (e) {
    showToast("Erro de ligação ao servidor", true);
  }
}

// ── MODO EDIÇÃO ──────────────────────────────────────────────────────────
let modoEdicaoId = null; // null = novo registo, número = a editar

async function editarRegisto(id) {
  showToast("A carregar registo...");
  const res = await fetch(`/api/registos/${id}`);
  const r = await res.json();

  limparFormulario();

  // preenche campos simples
  const campos = [
    "data","central","carro_n","marca","matricula","empresa","numero",
    "hora_entrada","hora_almoco","hora_saida","horas_extras",
    "km_inicio","km_fim","km_percorridos",
    "horas_iniciais_motor","horas_finais_motor",
    "horas_iniciais_bomba","horas_finais_bomba",
    "hora_ligou","hora_desligou","horas_motor_desligou",
    "motorista_nome","responsavel","observacoes",
    "oleo_motor_notas","oleo_sis_notas","agua_rad_notas",
  ];
  campos.forEach(id => { if ($(id) && r[id] !== undefined) $(id).value = r[id] || ""; });

  // checkboxes
  const checks = [
    "viatura_limpa_int","viatura_limpa_ext","viatura_lubrificada",
    "oleo_motor_ok","oleo_motor_naook","oleo_sis_ok","oleo_sis_naook",
    "agua_rad_ok","agua_rad_naook",
  ];
  checks.forEach(id => { if ($(id)) $(id).checked = !!r[id]; });

  // obras
  (r.obras || []).forEach(o => addObra(o));

  // gasóleo
  (r.gasoleo || []).forEach(g => addGasoleo(g));

  // activa modo edição
  modoEdicaoId = id;
  $("btn-guardar").textContent = "Guardar Alterações";
  $("btn-guardar").style.background = "#d97706"; // laranja para distinguir
  $("edit-banner").style.display = "flex";

  // vai para o formulário
  showView("form");
  window.scrollTo(0, 0);
  showToast("A editar folha nº" + r.numero);
}

function cancelarEdicao() {
  modoEdicaoId = null;
  $("btn-guardar").textContent = "Guardar Registo";
  $("btn-guardar").style.background = "";
  $("edit-banner").style.display = "none";
  limparFormulario();
  preencherComUltimoRegisto();
}

// ── HISTÓRICO ────────────────────────────────────────────────────────────
async function carregarHistorico() {
  const el = $("history-list");
  el.innerHTML = '<p style="color:#aaa;padding:20px">A carregar...</p>';
  try {
    const res = await fetch("/api/registos");
    const registos = await res.json();
    if (!registos.length) {
      el.innerHTML = '<div class="empty">Ainda não há registos guardados.</div>';
      return;
    }
    el.innerHTML = registos.map(r => {
      const d = new Date(r.data + "T12:00:00");
      const dateStr = d.toLocaleDateString("pt-PT", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
      return `
        <div class="history-card">
          <div>
            <div class="history-date">${dateStr}</div>
            <div class="history-meta">${r.matricula} · Folha nº${r.numero} · ${r.motorista_nome}</div>
            <div class="history-meta">${r.n_obras} obra(s) · ${r.total_m3} m³ total</div>
          </div>
          <div class="history-actions">
            <button class="btn-edit" onclick="editarRegisto(${r.id})">✏ Editar</button>
            <button class="btn-pdf" onclick="exportarPDF(${r.id}, '${r.data}', '${r.numero}')">⬇ PDF</button>
            <button class="btn-danger" style="font-size:18px" onclick="apagarRegisto(${r.id})" title="Apagar">×</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    el.innerHTML = '<div class="empty">Erro ao carregar histórico.</div>';
  }
}

async function exportarPDF(id, data, numero) {
  showToast("A gerar PDF...");
  window.open(`/api/registos/${id}/pdf`, "_blank");
}

async function apagarRegisto(id) {
  if (!confirm("Tens a certeza que queres apagar este registo?")) return;
  const res = await fetch(`/api/registos/${id}`, { method: "DELETE" });
  if (res.ok) {
    showToast("Registo apagado");
    carregarHistorico();
  }
}

// ── MÁSCARA HH:MM EM TODOS OS CAMPOS DE HORA ─────────────────────────────
// Funciona em desktop e mobile: type=text com inputmode=numeric
// Ao digitar 4 dígitos formata HH:MM e avança para o campo seguinte

function aplicarMascaraHora(input) {
  input.type = "text";
  input.setAttribute("inputmode", "numeric");
  input.setAttribute("placeholder", "HH:MM");
  input.setAttribute("maxlength", "5");

  input.addEventListener("input", function() {
    const cursor = this.selectionStart;
    let v = this.value.replace(/\D/g, "").slice(0, 4);

    // formata com ":"
    if (v.length >= 3) v = v.slice(0, 2) + ":" + v.slice(2);

    this.value = v;

    // ao completar HH:MM avança para o próximo campo
    if (v.length === 5) {
      const todos = Array.from(document.querySelectorAll("#view-form input, #view-form select, #view-form textarea"));
      const idx = todos.indexOf(this);
      if (idx >= 0 && todos[idx + 1]) todos[idx + 1].focus();
    }
  });

  // backspace limpa só dígitos (ignora o ":")
  input.addEventListener("keydown", function(e) {
    if (e.key === "Backspace" && this.value.endsWith(":")) {
      e.preventDefault();
      this.value = this.value.slice(0, -1);
    }
  });
}

function aplicarMascarasCartao(card) {
  card.querySelectorAll("input[type=time], input[data-hora]").forEach(aplicarMascaraHora);
}

function aplicarMascarasFormulario() {
  document.querySelectorAll("#view-form input[type=time]").forEach(aplicarMascaraHora);
}

aplicarMascarasFormulario();

// ── LIMPAR ───────────────────────────────────────────────────────────────
function limparFormulario() {
  ["km_inicio","km_fim","km_percorridos","horas_iniciais_motor","horas_finais_motor",
   "horas_iniciais_bomba","horas_finais_bomba","hora_entrada","hora_almoco","hora_saida",
   "horas_extras","hora_ligou","hora_desligou","horas_motor_desligou",
   "oleo_motor_notas","oleo_sis_notas","agua_rad_notas","observacoes","responsavel"
  ].forEach(id => { if ($(id)) $(id).value = ""; });

  ["viatura_limpa_int","viatura_limpa_ext","viatura_lubrificada",
   "oleo_motor_ok","oleo_motor_naook","oleo_sis_ok","oleo_sis_naook",
   "agua_rad_ok","agua_rad_naook"
  ].forEach(id => { if ($(id)) $(id).checked = false; });

  $("obras-body").innerHTML = "";
  $("gasoleo-body").innerHTML = "";
  obraId = 0; gasId = 0;
  updateTotal();
  $("data").value = new Date().toISOString().split("T")[0];
}
