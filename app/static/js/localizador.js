(function () {
  const form = document.getElementById("form-localizador");
  const statusEl = document.getElementById("localizador-status");
  const resultsEl = document.getElementById("localizador-resultados");
  const ufSelect = document.getElementById("f-uf");
  const cidadeInput = document.getElementById("f-cidade");
  const cidadeList = document.getElementById("f-cidade-sugestoes");

  function escapeHtml(str) {
    return (str ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function toTitleCase(str) {
    return (str ?? "")
      .toLowerCase()
      .replace(/(^|\s|\/|-)\p{L}/gu, (c) => c.toUpperCase());
  }

  function normalize(str) {
    return (str ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function bancoCardHtml(b) {
    const actions = [];
    if (b.tel_link) {
      actions.push(`<a href="${b.tel_link}">📞 Ligar</a>`);
    }
    if (b.whatsapp_link) {
      actions.push(`<a href="${b.whatsapp_link}" target="_blank" rel="noopener">💬 WhatsApp</a>`);
    }
    const telefoneTxt = b.telefone_fmt ? escapeHtml(b.telefone_fmt) : "Telefone não informado";

    return `
      <article class="banco-card">
        <span class="banco-categoria">${escapeHtml(b.categoria || "")}</span>
        <h3>${escapeHtml(b.nome)}</h3>
        <p class="banco-endereco">${escapeHtml(b.endereco || "")}, ${escapeHtml(b.cidade || "")} - ${escapeHtml(b.uf || "")}${b.cep ? ", CEP " + escapeHtml(b.cep) : ""}</p>
        <p class="banco-endereco">${telefoneTxt}</p>
        <div class="banco-actions">${actions.join("")}</div>
      </article>
    `;
  }

  async function search(params) {
    statusEl.textContent = "Buscando...";
    resultsEl.innerHTML = "";

    const qs = new URLSearchParams();
    if (params.uf) qs.set("uf", params.uf);
    if (params.cidade) qs.set("cidade", params.cidade);
    if (params.categoria) qs.set("categoria", params.categoria);

    try {
      const resp = await fetch(`/api/localizador?${qs.toString()}`);
      if (!resp.ok) throw new Error("Falha na busca");
      const data = await resp.json();

      if (data.total === 0) {
        statusEl.textContent = "Nenhum resultado encontrado para esses filtros.";
        return;
      }

      statusEl.textContent = `${data.total} resultado(s) encontrado(s).`;
      resultsEl.innerHTML = data.resultados.map(bancoCardHtml).join("");
    } catch (err) {
      statusEl.textContent = "Erro ao buscar. Tente novamente.";
    }
  }

  function currentParams() {
    return {
      uf: ufSelect.value,
      cidade: cidadeInput.value,
      categoria: document.getElementById("f-categoria").value,
    };
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    closeSuggestions();
    search(currentParams());
  });

  // ---- Autocomplete de cidade ----
  let cidadesCache = [];
  let activeIndex = -1;

  async function loadCidades(uf) {
    const qs = uf ? `?uf=${encodeURIComponent(uf)}` : "";
    try {
      const resp = await fetch(`/api/cidades${qs}`);
      const data = await resp.json();
      cidadesCache = data.cidades || [];
    } catch (err) {
      cidadesCache = [];
    }
  }

  function closeSuggestions() {
    cidadeList.hidden = true;
    cidadeList.innerHTML = "";
    activeIndex = -1;
  }

  function highlightMatch(cidade, query) {
    const display = toTitleCase(cidade);
    const idx = normalize(display).indexOf(normalize(query));
    if (idx === -1 || !query) return escapeHtml(display);
    const before = display.slice(0, idx);
    const match = display.slice(idx, idx + query.length);
    const after = display.slice(idx + query.length);
    return `${escapeHtml(before)}<mark>${escapeHtml(match)}</mark>${escapeHtml(after)}`;
  }

  function renderSuggestions(query) {
    const q = normalize(query);
    if (!q) {
      closeSuggestions();
      return;
    }

    const matches = cidadesCache
      .filter((c) => normalize(c).includes(q))
      .slice(0, 8);

    if (matches.length === 0) {
      closeSuggestions();
      return;
    }

    cidadeList.innerHTML = matches
      .map((c, i) => `<li data-value="${escapeHtml(toTitleCase(c))}" data-index="${i}">${highlightMatch(c, query)}</li>`)
      .join("");
    cidadeList.hidden = false;
    activeIndex = -1;
  }

  function setActive(index) {
    const items = cidadeList.querySelectorAll("li");
    items.forEach((li) => li.classList.remove("active"));
    if (index >= 0 && index < items.length) {
      items[index].classList.add("active");
      items[index].scrollIntoView({ block: "nearest" });
      activeIndex = index;
    }
  }

  cidadeInput.addEventListener("input", () => {
    renderSuggestions(cidadeInput.value);
  });

  cidadeInput.addEventListener("focus", () => {
    if (cidadeInput.value) renderSuggestions(cidadeInput.value);
  });

  cidadeInput.addEventListener("keydown", (e) => {
    const items = cidadeList.querySelectorAll("li");
    if (cidadeList.hidden || items.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((activeIndex + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((activeIndex - 1 + items.length) % items.length);
    } else if (e.key === "Enter") {
      if (activeIndex >= 0) {
        e.preventDefault();
        cidadeInput.value = items[activeIndex].dataset.value;
        closeSuggestions();
      }
    } else if (e.key === "Escape") {
      closeSuggestions();
    }
  });

  cidadeList.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (!li) return;
    cidadeInput.value = li.dataset.value;
    closeSuggestions();
    search(currentParams());
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".autocomplete")) closeSuggestions();
  });

  ufSelect.addEventListener("change", () => {
    cidadeInput.value = "";
    closeSuggestions();
    loadCidades(ufSelect.value);
  });

  // ---- Inicialização ----
  const initial = new URLSearchParams(window.location.search);
  let hasInitial = false;
  if (initial.get("uf")) {
    ufSelect.value = initial.get("uf");
    hasInitial = true;
  }
  if (initial.get("cidade")) {
    cidadeInput.value = initial.get("cidade");
    hasInitial = true;
  }
  if (initial.get("categoria")) {
    document.getElementById("f-categoria").value = initial.get("categoria");
    hasInitial = true;
  }

  loadCidades(ufSelect.value);
  search(hasInitial ? currentParams() : {});
})();
