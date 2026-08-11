if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {
      // Contexto não seguro (http:// em IP de rede local) — instalação manual
      // via "Adicionar à tela inicial" ainda funciona, sem cache offline completo.
    });
  });
}
