(function () {
  "use strict";

  /* ---------------------------------------------------------------------
   * Toast helper
   * ------------------------------------------------------------------- */
  const toastStack = document.getElementById("toast-stack");

  function showToast(message, tag) {
    if (!toastStack || !message) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    if (tag === "error") toast.style.borderColor = "#E63946";
    toast.textContent = message;
    toastStack.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("is-leaving");
      setTimeout(() => toast.remove(), 260);
    }, 3200);
  }

  // Show any Django messages rendered server-side as toasts.
  document.querySelectorAll(".hidden-messages [data-toast]").forEach((el) => {
    showToast(el.getAttribute("data-toast"), el.getAttribute("data-tag"));
  });

  /* ---------------------------------------------------------------------
   * Mobile menu
   * ------------------------------------------------------------------- */
  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobile-menu");

  if (hamburger && mobileMenu) {
    hamburger.addEventListener("click", () => {
      const isOpen = !mobileMenu.hidden;
      mobileMenu.hidden = isOpen;
      hamburger.setAttribute("aria-expanded", String(!isOpen));
      document.body.style.overflow = isOpen ? "" : "hidden";
    });

    mobileMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        mobileMenu.hidden = true;
        hamburger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });
  }

  /* ---------------------------------------------------------------------
   * Scroll reveal
   * ------------------------------------------------------------------- */
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach((el) => observer.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------------------------------------------------------------------
   * Countdown timers (promo banners)
   * ------------------------------------------------------------------- */
  function formatCountdown(ms) {
    if (ms <= 0) return "Encerrada";
    const totalSeconds = Math.floor(ms / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const pad = (n) => String(n).padStart(2, "0");
    if (days > 0) return `${days}d ${pad(hours)}h ${pad(minutes)}m`;
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }

  const countdowns = document.querySelectorAll(".countdown[data-ends]");
  if (countdowns.length) {
    const tick = () => {
      countdowns.forEach((el) => {
        const endsAt = new Date(el.getAttribute("data-ends")).getTime();
        const valueEl = el.querySelector(".countdown__value");
        if (!valueEl) return;
        valueEl.textContent = formatCountdown(endsAt - Date.now());
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  /* ---------------------------------------------------------------------
   * Add to cart via AJAX (progressive enhancement)
   * ------------------------------------------------------------------- */
  const cartCountEl = document.getElementById("cart-count");

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  document.querySelectorAll(".add-to-cart-form").forEach((form) => {
    function handleSubmit(event) {
      // "Comprar agora" forms include a hidden buy_now field: let the
      // browser follow the normal redirect flow straight to checkout.
      if (form.querySelector('input[name="buy_now"]')) return;

      event.preventDefault();
      const formData = new FormData(form);
      const productName = form.getAttribute("data-product-name") || "Item";

      fetch(form.action, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken") || formData.get("csrfmiddlewaretoken"),
        },
        body: formData,
      })
        .then((response) => {
          if (!response.ok) throw new Error("network");
          return response.json();
        })
        .then((data) => {
          if (cartCountEl) {
            cartCountEl.textContent = data.cart_count;
            cartCountEl.classList.remove("bump");
            void cartCountEl.offsetWidth;
            cartCountEl.classList.add("bump");
          }
          showToast(data.message || `${productName} adicionado ao carrinho!`);
        })
        .catch(() => {
          // Fallback: submit normally if the AJAX call fails for any reason.
          form.removeEventListener("submit", handleSubmit);
          form.submit();
        });
    }

    form.addEventListener("submit", handleSubmit);
  });
})();
