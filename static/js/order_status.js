(() => {
  const card = document.getElementById("order-status-card");
  if (!card) return;

  document.getElementById("copy-pix")?.addEventListener("click", async (event) => {
    const code = document.getElementById("pix-code")?.value || "";
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      event.currentTarget.textContent = "Copiado!";
      setTimeout(() => { event.currentTarget.textContent = "Copiar código"; }, 1800);
    } catch (_) {
      document.getElementById("pix-code")?.select();
    }
  });

  const statusUrl = card.dataset.statusUrl;
  const label = document.getElementById("payment-status-label");
  if (!statusUrl || !label || !["Aguardando pagamento"].includes(label.textContent.trim())) return;

  let attempts = 0;
  const poll = async () => {
    attempts += 1;
    try {
      const response = await fetch(statusUrl, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      label.textContent = data.statusLabel;
      if (data.status === "PAID") {
        window.location.reload();
        return;
      }
      if (["REJECTED", "CANCELLED", "REFUNDED", "ERROR"].includes(data.status)) {
        window.location.reload();
        return;
      }
    } catch (_) {
      // Uma falha temporária de rede não invalida o pagamento.
    }
    if (attempts < 120) setTimeout(poll, 5000);
  };
  setTimeout(poll, 5000);
})();
