(() => {
  const menu = document.getElementById("menu");
  const menuToggle = document.getElementById("menu-toggle");
  const menuClose = document.getElementById("menu-close");
  const menuLinks = menu ? menu.querySelectorAll("a") : [];
  const form = document.getElementById("emailForm");
  const formStatus = document.getElementById("form-status");

  const setMenuState = (isOpen) => {
    if (!menu || !menuToggle) return;
    menu.classList.toggle("is-open", isOpen);
    menu.setAttribute("aria-hidden", String(!isOpen));
    menuToggle.setAttribute("aria-expanded", String(isOpen));
  };

  if (menu && menuToggle && menuClose) {
    menuToggle.addEventListener("click", () => setMenuState(true));
    menuClose.addEventListener("click", () => setMenuState(false));

    menu.addEventListener("click", (event) => {
      if (event.target === menu) {
        setMenuState(false);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        setMenuState(false);
      }
    });

    for (const link of menuLinks) {
      link.addEventListener("click", () => setMenuState(false));
    }
  }

  if (!form || !formStatus) return;

  const setStatus = (message, isError = false) => {
    formStatus.textContent = message;
    formStatus.classList.toggle("error", isError);
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      message: String(formData.get("message") || "").trim()
    };

    if (!payload.name || !payload.email || !payload.message) {
      setStatus("Please fill out name, email, and message.", true);
      return;
    }

    const submitButton = form.querySelector("button[type='submit']");
    if (submitButton) submitButton.disabled = true;
    setStatus("Sending message...");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Contact form request failed");
      }

      form.reset();
      setStatus("Thanks! Your message has been sent.");
    } catch (error) {
      setStatus("Sorry, message failed. Please call us at (612) 390-7483.", true);
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  });
})();
