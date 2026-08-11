(function () {
  const form = document.getElementById("form-doadora");
  const feedback = document.getElementById("form-feedback");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    feedback.textContent = "Enviando...";
    feedback.className = "form-feedback";

    const fd = new FormData(form);
    const payload = {
      nome: fd.get("nome"),
      email: fd.get("email"),
      telefone: fd.get("telefone"),
      cidade: fd.get("cidade"),
      uf: fd.get("uf"),
      bebe_nascimento: fd.get("bebe_nascimento") || null,
      ja_doou_antes: fd.get("ja_doou_antes") === "on",
      mensagem: fd.get("mensagem") || null,
    };

    try {
      const resp = await fetch("/api/doadoras", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (resp.status === 201) {
        form.reset();
        feedback.textContent = "Cadastro recebido com sucesso! Em breve entraremos em contato. Obrigado por doar. 💙";
        feedback.className = "form-feedback success";
      } else {
        const err = await resp.json().catch(() => null);
        feedback.textContent = err?.detail?.[0]?.msg || "Verifique os campos preenchidos e tente novamente.";
        feedback.className = "form-feedback error";
      }
    } catch (err) {
      feedback.textContent = "Não foi possível enviar agora. Tente novamente em instantes.";
      feedback.className = "form-feedback error";
    }
  });
})();
