(function () {
  const container = document.getElementById("mapa-bancos");
  if (!container || typeof L === "undefined") return;

  const map = L.map(container, { scrollWheelZoom: false }).setView([-14.2, -51.9], 4);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(map);

  const markersLayer = L.layerGroup().addTo(map);
  const DEFAULT_VIEW = { center: [-14.2, -51.9], zoom: 4 };
  let requestId = 0;

  function render(pontos, hasFiltro) {
    markersLayer.clearLayers();
    pontos.forEach((ponto) => {
      const marker = L.circleMarker([ponto.lat, ponto.lng], {
        radius: 5 + Math.min(ponto.total, 10),
        color: "#1565c0",
        fillColor: "#1565c0",
        fillOpacity: 0.6,
        weight: 1,
      });

      const nomes = ponto.nomes.map((n) => `<li>${n}</li>`).join("");
      marker.bindPopup(`
        <div class="map-popup">
          <strong>${ponto.cidade} — ${ponto.uf}</strong>
          <p>${ponto.total} ponto(s) de coleta</p>
          <ul>${nomes}</ul>
        </div>
      `);
      markersLayer.addLayer(marker);
    });

    if (hasFiltro && pontos.length > 0) {
      const bounds = L.latLngBounds(pontos.map((p) => [p.lat, p.lng]));
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 });
    } else if (!hasFiltro) {
      map.setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
    }
  }

  function refresh(params) {
    const qs = new URLSearchParams();
    if (params?.uf) qs.set("uf", params.uf);
    if (params?.cidade) qs.set("cidade", params.cidade);
    if (params?.categoria) qs.set("categoria", params.categoria);
    const hasFiltro = Boolean(params?.uf || params?.cidade || params?.categoria);

    const myRequestId = ++requestId;
    fetch(`${container.dataset.endpoint}?${qs.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        if (myRequestId !== requestId) return; // resposta antiga, ignora
        render(data.pontos || [], hasFiltro);
      })
      .catch(() => {});
  }

  window.mapaBancos = { refresh };
  refresh({});
})();
