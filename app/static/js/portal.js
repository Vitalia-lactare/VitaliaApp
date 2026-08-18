(function () {
  const STEP_ORDER = [
    "boas_vindas", "video",
    "quiz_q1", "quiz_q2", "quiz_q3", "quiz_q4", "quiz_q5", "quiz_q6",
    "cadastro", "confirmacao", "agendamento", "feedback", "fechamento",
  ];

  const state = {
    sessaoId: null,
    currentIndex: 0,
    respostas: {},
    cadastro: { cepResolved: false, cidade: null, uf: null, bancoEncontrado: null },
    doadoraId: null,
  };

  state.sessaoId = sessionStorage.getItem("vitalia_sessao_id") || crypto.randomUUID();
  sessionStorage.setItem("vitalia_sessao_id", state.sessaoId);

  const steps = {};
  document.querySelectorAll(".wizard-step").forEach((el) => {
    steps[el.dataset.step] = el;
  });

  const progressbar = document.getElementById("wizard-progressbar");
  const progressbarFill = document.getElementById("wizard-progressbar-fill");
  const progressbarLabel = document.getElementById("wizard-progressbar-label");

  function escapeHtml(str) {
    return (str ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function logEvento(evento, etapa = null, metadata = null) {
    fetch("/api/portal/eventos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
      body: JSON.stringify({ sessao_id: state.sessaoId, evento, etapa, metadata }),
    }).catch(() => {});
  }

  const VIEW_EVENTS = {
    boas_vindas: "boas_vindas_view",
    video: "video_view",
    cadastro: "cadastro_view",
    confirmacao: "confirmacao_view",
    agendamento: "agendamento_view",
    feedback: "feedback_view",
    fechamento: "fechamento_view",
  };

  function goToStep(index) {
    const stepName = STEP_ORDER[index];
    Object.values(steps).forEach((el) => { el.hidden = true; });
    steps[stepName].hidden = false;
    state.currentIndex = index;
    window.scrollTo({ top: 0, behavior: "smooth" });
    updateProgressbar(stepName);

    if (stepName.startsWith("quiz_q")) {
      const quizIndex = steps[stepName].dataset.quizIndex;
      logEvento("quiz_step_view", `q${quizIndex}`);
    } else if (VIEW_EVENTS[stepName]) {
      logEvento(VIEW_EVENTS[stepName]);
    }
  }

  function updateProgressbar(stepName) {
    if (stepName.startsWith("quiz_q")) {
      const quizIndex = Number(steps[stepName].dataset.quizIndex);
      progressbar.hidden = false;
      progressbarFill.style.width = `${(quizIndex / 6) * 100}%`;
      progressbarLabel.textContent = `Pergunta ${quizIndex} de 6`;
    } else {
      progressbar.hidden = true;
    }
  }

  function goNext() {
    if (state.currentIndex < STEP_ORDER.length - 1) goToStep(state.currentIndex + 1);
  }
  function goBack() {
    if (state.currentIndex > 0) goToStep(state.currentIndex - 1);
  }

  document.querySelectorAll("[data-wizard-next]").forEach((btn) => {
    btn.addEventListener("click", goNext);
  });
  document.querySelectorAll("[data-wizard-back]").forEach((btn) => {
    btn.addEventListener("click", goBack);
  });

  // ---- Quiz ----
  function parseValue(raw) {
    if (raw === "true") return true;
    if (raw === "false") return false;
    return raw;
  }

  document.querySelectorAll(".quiz-options").forEach((group) => {
    const field = group.dataset.quizField;
    group.querySelectorAll(".quiz-option").forEach((btn) => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".quiz-option").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        state.respostas[field] = parseValue(btn.dataset.value);

        if (field === "ja_doou_antes") {
          submitTriagem();
        } else {
          goNext();
        }
      });
    });
  });

  async function submitTriagem() {
    try {
      await fetch("/api/portal/triagem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessao_id: state.sessaoId, ...state.respostas }),
      });
    } catch (e) { /* melhor esforco, nunca bloqueia o wizard */ }
    logEvento("quiz_completed");
    goToStep(STEP_ORDER.indexOf("cadastro"));
  }

  // ---- Cadastro: CEP + fallback manual ----
  const cepInput = document.getElementById("cad-cep");
  const cepStatus = document.getElementById("cad-cep-status");
  const bancoEncontradoEl = document.getElementById("cad-banco-encontrado");
  const manualBlock = document.getElementById("cad-manual");
  const ufSelect = document.getElementById("cad-uf");
  const cidadeInput = document.getElementById("cad-cidade");
  const cidadeList = document.getElementById("cad-cidade-sugestoes");

  function normalize(str) {
    return (str ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }
  function toTitleCase(str) {
    return (str ?? "").toLowerCase().replace(/(^|\s|\/|-)\p{L}/gu, (c) => c.toUpperCase());
  }

  function bancoCardHtml(b) {
    const tipoTxt = b.match_tipo === "cidade"
      ? "Ponto de coleta na sua cidade:"
      : "Ponto de coleta mais próximo no seu estado:";
    return `
      <p class="form-hint">${tipoTxt}</p>
      <span class="banco-categoria">${escapeHtml(b.categoria || "")}</span>
      <h3>${escapeHtml(b.nome)}</h3>
      <p class="banco-endereco">${escapeHtml(b.endereco || "")}, ${escapeHtml(b.cidade || "")} - ${escapeHtml(b.uf || "")}</p>
      ${b.telefone_fmt ? `<p class="banco-endereco">${escapeHtml(b.telefone_fmt)}</p>` : ""}
    `;
  }

  let cidadesCache = [];
  async function loadCidades(uf) {
    try {
      const resp = await fetch(`/api/cidades?uf=${encodeURIComponent(uf)}`);
      const data = await resp.json();
      cidadesCache = data.cidades || [];
    } catch (e) {
      cidadesCache = [];
    }
  }

  function renderCidadeSugestoes(query) {
    const q = normalize(query);
    if (!q) { cidadeList.hidden = true; cidadeList.innerHTML = ""; return; }
    const matches = cidadesCache.filter((c) => normalize(c).includes(q)).slice(0, 8);
    if (matches.length === 0) { cidadeList.hidden = true; cidadeList.innerHTML = ""; return; }
    cidadeList.innerHTML = matches
      .map((c) => `<li data-value="${escapeHtml(toTitleCase(c))}">${escapeHtml(toTitleCase(c))}</li>`)
      .join("");
    cidadeList.hidden = false;
  }

  if (cidadeInput) {
    cidadeInput.addEventListener("input", () => renderCidadeSugestoes(cidadeInput.value));
    cidadeList.addEventListener("click", (e) => {
      const li = e.target.closest("li");
      if (!li) return;
      cidadeInput.value = li.dataset.value;
      cidadeList.hidden = true;
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".autocomplete")) cidadeList.hidden = true;
    });
  }

  if (ufSelect) {
    ufSelect.addEventListener("change", () => {
      cidadeInput.value = "";
      if (ufSelect.value) loadCidades(ufSelect.value);
    });
  }

  function showManualFallback() {
    manualBlock.hidden = false;
    bancoEncontradoEl.hidden = true;
  }

  if (cepInput) {
    cepInput.addEventListener("input", async () => {
      const digits = cepInput.value.replace(/\D/g, "");
      if (digits.length !== 8) {
        state.cadastro.cepResolved = false;
        cepStatus.textContent = "";
        return;
      }

      cepStatus.textContent = "Buscando localização...";
      try {
        const resp = await fetch(`/api/portal/cep?cep=${digits}`);
        const data = await resp.json();

        if (data.encontrado) {
          state.cadastro = { cepResolved: true, cidade: data.cidade, uf: data.uf, bancoEncontrado: data.banco };
          cepStatus.textContent = `${data.cidade} - ${data.uf}`;
          manualBlock.hidden = true;
          if (data.banco) {
            bancoEncontradoEl.innerHTML = bancoCardHtml(data.banco);
            bancoEncontradoEl.hidden = false;
          } else {
            bancoEncontradoEl.hidden = true;
          }
        } else {
          state.cadastro.cepResolved = false;
          cepStatus.textContent = "Não encontramos esse CEP — preencha manualmente abaixo.";
          showManualFallback();
        }
      } catch (e) {
        state.cadastro.cepResolved = false;
        cepStatus.textContent = "Não foi possível verificar o CEP agora — preencha manualmente.";
        showManualFallback();
      }
    });
  }

  // ---- Cadastro: submit ----
  const formCadastro = document.getElementById("form-cadastro");
  const cadFeedback = document.getElementById("cad-feedback");
  const confBancoCard = document.getElementById("conf-banco-card");

  if (formCadastro) {
    formCadastro.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(formCadastro);

      const cidade = state.cadastro.cepResolved ? state.cadastro.cidade : cidadeInput.value;
      const uf = state.cadastro.cepResolved ? state.cadastro.uf : ufSelect.value;

      if (!cidade || !uf) {
        cadFeedback.textContent = "Informe seu CEP ou preencha cidade/estado manualmente.";
        cadFeedback.className = "form-feedback error";
        return;
      }

      const payload = {
        sessao_id: state.sessaoId,
        nome: fd.get("nome"),
        email: fd.get("email"),
        telefone: fd.get("telefone"),
        cep: fd.get("cep"),
        cidade,
        uf,
        bebe_nascimento: fd.get("bebe_nascimento") || null,
        ja_doou_antes: state.respostas.ja_doou_antes === true,
        mensagem: fd.get("mensagem") || null,
        banco_leite_id: state.cadastro.bancoEncontrado ? state.cadastro.bancoEncontrado.id : null,
      };

      cadFeedback.textContent = "Enviando...";
      cadFeedback.className = "form-feedback";

      try {
        const resp = await fetch("/api/portal/cadastro", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (resp.status === 201) {
          const body = await resp.json();
          state.doadoraId = body.id;
          confBancoCard.innerHTML = body.banco
            ? bancoCardHtml(body.banco)
            : "<p>Em breve nossa equipe indica o ponto de coleta ideal para você.</p>";
          logEvento("cadastro_submitted");
          formCadastro.reset();
          cadFeedback.textContent = "";
          goToStep(STEP_ORDER.indexOf("confirmacao"));
        } else {
          logEvento("cadastro_error", null, { status: resp.status });
          cadFeedback.textContent = "Verifique os campos preenchidos e tente novamente.";
          cadFeedback.className = "form-feedback error";
        }
      } catch (err) {
        logEvento("cadastro_error", null, { status: 0 });
        cadFeedback.textContent = "Não foi possível enviar agora. Tente novamente.";
        cadFeedback.className = "form-feedback error";
      }
    });
  }

  // ---- Agendamento ----
  const formAgendamento = document.getElementById("form-agendamento");
  const agFeedback = document.getElementById("ag-feedback");

  if (formAgendamento) {
    formAgendamento.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(formAgendamento);
      agFeedback.textContent = "Enviando...";
      agFeedback.className = "form-feedback";

      try {
        const resp = await fetch("/api/portal/agendamento", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            doadora_id: state.doadoraId,
            sessao_id: state.sessaoId,
            endereco_coleta: fd.get("endereco_coleta"),
            data_preferida: fd.get("data_preferida") || null,
            periodo: fd.get("periodo") || null,
          }),
        });
        if (resp.ok) {
          goToStep(STEP_ORDER.indexOf("feedback"));
        } else {
          agFeedback.textContent = "Verifique os campos e tente novamente.";
          agFeedback.className = "form-feedback error";
        }
      } catch (err) {
        agFeedback.textContent = "Não foi possível enviar agora. Tente novamente.";
        agFeedback.className = "form-feedback error";
      }
    });
  }

  const skipAgendamento = document.querySelector("[data-agendamento-skip]");
  if (skipAgendamento) {
    skipAgendamento.addEventListener("click", () => {
      logEvento("agendamento_skipped");
      goToStep(STEP_ORDER.indexOf("feedback"));
    });
  }

  // ---- Feedback ----
  const formFeedback = document.getElementById("form-feedback");
  if (formFeedback) {
    formFeedback.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(formFeedback);
      const nota = fd.get("nota");
      if (!nota) return;

      try {
        await fetch("/api/portal/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            doadora_id: state.doadoraId,
            sessao_id: state.sessaoId,
            nota: Number(nota),
            comentario: fd.get("comentario") || null,
          }),
        });
      } catch (err) { /* melhor esforco */ }
      goToStep(STEP_ORDER.indexOf("fechamento"));
    });
  }

  const skipFeedback = document.querySelector("[data-feedback-skip]");
  if (skipFeedback) {
    skipFeedback.addEventListener("click", () => {
      goToStep(STEP_ORDER.indexOf("fechamento"));
    });
  }

  // ---- Fechamento: saiba mais ----
  document.querySelectorAll("[data-saiba-mais]").forEach((link) => {
    link.addEventListener("click", () => {
      logEvento("saiba_mais_click", link.dataset.saibaMais);
    });
  });

  // ---- Inicializacao ----
  goToStep(0);
})();
