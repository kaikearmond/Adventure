(() => {
  const configNode = document.getElementById("checkout-config");
  if (!configNode) return;

  const config = JSON.parse(configNode.textContent);
  const buyerForm = document.getElementById("buyer-data-form");
  const paymentSection = document.getElementById("checkout-payment");
  const editButton = document.getElementById("edit-buyer-data");
  const feedback = document.getElementById("payment-feedback");
  const nameInput = document.getElementById("buyer-name");
  const emailInput = document.getElementById("buyer-email");
  const cpfInput = document.getElementById("buyer-cpf");
  const csrfInput = buyerForm?.querySelector("input[name='csrfmiddlewaretoken']");

  let brickController = null;
  let buyerData = null;
  function createAttemptId() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    const bytes = new Uint8Array(16);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (let index = 0; index < bytes.length; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
      }
    }
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }

  const attemptId = createAttemptId();

  function onlyDigits(value) {
    return (value || "").replace(/\D/g, "");
  }

  function formatCpf(value) {
    const digits = onlyDigits(value).slice(0, 11);
    return digits
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");
  }

  cpfInput?.addEventListener("input", () => {
    cpfInput.value = formatCpf(cpfInput.value);
  });

  function showFeedback(message, type = "info") {
    if (!feedback) return;
    feedback.textContent = message;
    feedback.dataset.type = type;
  }

  function validateBuyer() {
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const cpf = onlyDigits(cpfInput.value);
    if (name.length < 3) {
      nameInput.focus();
      return { error: "Informe seu nome completo." };
    }
    if (!emailInput.checkValidity()) {
      emailInput.focus();
      return { error: "Informe um e-mail válido." };
    }
    if (cpf.length !== 11 || new Set(cpf).size === 1) {
      cpfInput.focus();
      return { error: "Informe um CPF válido com 11 dígitos." };
    }
    return { name, email, cpf };
  }

  async function mountBrick() {
    if (!config.enabled) {
      paymentSection.hidden = false;
      paymentSection.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (typeof MercadoPago === "undefined") {
      showFeedback("Não foi possível carregar o Mercado Pago. Atualize a página.", "error");
      return;
    }
    if (brickController) {
      await brickController.unmount();
      brickController = null;
    }

    const mp = new MercadoPago(config.publicKey, { locale: "pt-BR" });
    const bricksBuilder = mp.bricks();
    const settings = {
      initialization: {
        amount: Number(config.amount),
        payer: {
          email: buyerData.email,
          identification: { type: "CPF", number: buyerData.cpf },
        },
      },
      customization: {
        paymentMethods: {
          creditCard: "all",
          bankTransfer: "pix",
          minInstallments: 1,
          maxInstallments: Number(config.maxInstallments || 6),
        },
      },
      callbacks: {
        onReady: () => showFeedback("Escolha Pix ou cartão para concluir a compra.", "success"),
        onSubmit: ({ formData }) => {
          showFeedback("Processando pagamento...", "info");
          return new Promise((resolve, reject) => {
            fetch(config.processUrl, {
              method: "POST",
              credentials: "same-origin",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfInput?.value || "",
              },
              body: JSON.stringify({
                attemptId,
                buyer: buyerData,
                formData,
              }),
            })
              .then(async (response) => {
                const result = await response.json().catch(() => ({}));
                if (!response.ok || !result.ok) {
                  throw new Error(result.error || "Não foi possível processar o pagamento.");
                }
                resolve();
                window.location.assign(result.orderUrl);
              })
              .catch((error) => {
                showFeedback(error.message || "Erro ao processar pagamento.", "error");
                reject(error);
              });
          });
        },
        onError: (error) => {
          console.error("Mercado Pago Brick:", error);
          showFeedback("O formulário de pagamento encontrou um erro. Tente novamente.", "error");
        },
      },
    };

    brickController = await bricksBuilder.create("payment", "paymentBrick_container", settings);
  }

  buyerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = validateBuyer();
    if (result.error) {
      alert(result.error);
      return;
    }
    buyerData = result;
    buyerForm.closest(".checkout-block").classList.add("is-complete");
    paymentSection.hidden = false;
    paymentSection.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      await mountBrick();
    } catch (error) {
      console.error(error);
      showFeedback("Não foi possível iniciar o checkout do Mercado Pago.", "error");
    }
  });

  editButton?.addEventListener("click", async () => {
    if (brickController) {
      await brickController.unmount();
      brickController = null;
    }
    paymentSection.hidden = true;
    buyerForm.closest(".checkout-block").classList.remove("is-complete");
    nameInput.focus();
  });

  window.addEventListener("beforeunload", () => {
    if (brickController) brickController.unmount();
  });
})();
