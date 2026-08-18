(function () {
  const toggle = document.getElementById("chat-toggle");
  const panel = document.getElementById("chat-panel");
  const closeBtn = document.getElementById("chat-close");
  const messagesEl = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");

  if (!toggle || !panel || !form) return;

  const historico = [];

  function addMessage(texto, autor) {
    const el = document.createElement("div");
    el.className = `chat-message chat-message-${autor}`;
    el.textContent = texto;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function openChat() {
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    input.focus();
  }

  function closeChat() {
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
  }

  toggle.addEventListener("click", () => {
    if (panel.hidden) openChat(); else closeChat();
  });
  closeBtn.addEventListener("click", closeChat);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const mensagem = input.value.trim();
    if (!mensagem) return;

    addMessage(mensagem, "user");
    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;
    const pensando = addMessage("Digitando...", "bot");
    pensando.classList.add("chat-message-pending");

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensagem, historico }),
      });
      const data = await resp.json();
      pensando.remove();

      if (resp.ok) {
        addMessage(data.resposta, "bot");
        historico.push({ role: "user", content: mensagem });
        historico.push({ role: "assistant", content: data.resposta });
        if (historico.length > 20) historico.splice(0, historico.length - 20);
      } else {
        addMessage("Não consegui responder agora. Tente novamente em instantes.", "bot");
      }
    } catch (err) {
      pensando.remove();
      addMessage("Não consegui me conectar agora. Verifique sua internet e tente de novo.", "bot");
    } finally {
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  });
})();
