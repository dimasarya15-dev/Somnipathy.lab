/* ============================================================
   Logika halaman deteksi:
   1. kumpulkan isian form
   2. validasi ringan di browser
   3. kirim ke POST /api/predict
   4. arahkan ke halaman hasil (server-rendered)
   ============================================================ */
(function () {
  "use strict";

  const form = document.getElementById("form-deteksi");
  if (!form) {
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  const resetButton = form.querySelector('button[type="reset"]');
  const messageBox = document.getElementById("pesan");
  const fallbackBox = document.getElementById("hasil-sementara");
  const modelReady = form.dataset.modelReady === "true";
  const originalButtonText = submitButton ? submitButton.textContent : "";

  form.addEventListener("submit", handleSubmit);

  if (resetButton) {
    resetButton.addEventListener("click", function () {
      clearAllErrors();
      hideMessage();
      if (fallbackBox) {
        fallbackBox.hidden = true;
        fallbackBox.innerHTML = "";
      }
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    clearAllErrors();
    hideMessage();

    if (!modelReady) {
      showMessage(
        "Model klasifikasi belum tersedia. Latih model terlebih dahulu, lalu jalankan ulang server.",
        "warning"
      );
      return;
    }

    const payload = collectPayload();
    const errors = validateLocally();

    if (Object.keys(errors).length > 0) {
      Object.entries(errors).forEach(function (entry) {
        showFieldError(entry[0], entry[1]);
      });
      showMessage("Periksa kembali isian yang ditandai merah.", "error");
      focusFirstError();
      return;
    }

    setLoading(true);

    try {
      const response = await window.SomnipathyApi.postJSON("/api/predict", payload);
      const data = response && response.data;

      if (!data) {
        throw new Error("Server tidak mengirim data hasil analisis.");
      }

      if (data.detection_id) {
        window.location.assign("/hasil/" + data.detection_id);
        return;
      }

      renderFallback(data);
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- Kumpulkan data ---------- */

  function collectPayload() {
    const payload = {};

    form.querySelectorAll("[data-field]").forEach(function (wrapper) {
      const input = wrapper.querySelector("input, select");
      if (!input || !input.name) {
        return;
      }
      const value = input.value.trim();
      payload[input.name] = value === "" ? null : value;
    });

    return payload;
  }

  /* ---------- Validasi di browser ---------- */

  function validateLocally() {
    const errors = {};

    form.querySelectorAll("[data-field]").forEach(function (wrapper) {
      const input = wrapper.querySelector("input, select");
      if (!input) {
        return;
      }

      const value = input.value.trim();

      if (input.required && value === "") {
        errors[input.name] = "Wajib diisi.";
        return;
      }

      if (input.type === "number" && value !== "") {
        const numeric = Number(value.replace(",", "."));
        if (Number.isNaN(numeric)) {
          errors[input.name] = "Harus berupa angka.";
          return;
        }
        if (input.min !== "" && numeric < Number(input.min)) {
          errors[input.name] = "Nilai minimal " + input.min + ".";
          return;
        }
        if (input.max !== "" && numeric > Number(input.max)) {
          errors[input.name] = "Nilai maksimal " + input.max + ".";
        }
      }
    });

    return errors;
  }

  /* ---------- Tampilan ---------- */

  function setLoading(isLoading) {
    form.setAttribute("aria-busy", isLoading ? "true" : "false");

    if (!submitButton) {
      return;
    }

    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading ? "Menganalisis…" : originalButtonText;
  }

  function showMessage(text, kind) {
    if (!messageBox) {
      return;
    }
    messageBox.textContent = text;
    messageBox.className = "alert alert--" + (kind || "info");
    messageBox.hidden = false;
    messageBox.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function hideMessage() {
    if (!messageBox) {
      return;
    }
    messageBox.hidden = true;
    messageBox.textContent = "";
  }

  function showFieldError(name, text) {
    const wrapper = form.querySelector('[data-field="' + name + '"]');
    if (!wrapper) {
      return;
    }
    wrapper.classList.add("has-error");
    const paragraph = wrapper.querySelector(".field-error");
    if (paragraph) {
      paragraph.textContent = text;
      paragraph.hidden = false;
    }
  }

  function clearAllErrors() {
    form.querySelectorAll(".field.has-error").forEach(function (wrapper) {
      wrapper.classList.remove("has-error");
      const paragraph = wrapper.querySelector(".field-error");
      if (paragraph) {
        paragraph.textContent = "";
        paragraph.hidden = true;
      }
    });
  }

  function focusFirstError() {
    const firstError = form.querySelector(".field.has-error input, .field.has-error select");
    if (firstError) {
      firstError.focus();
    }
  }

  function handleError(error) {
    if (error && error.errors) {
      Object.entries(error.errors).forEach(function (entry) {
        if (entry[0] === "_") {
          showMessage(entry[1], "error");
          return;
        }
        showFieldError(entry[0], entry[1]);
      });
      focusFirstError();
      return;
    }

    if (error && error.status === 503) {
      showMessage(error.message, "warning");
      return;
    }

    showMessage(
      (error && error.message) || "Terjadi kesalahan tak terduga. Coba lagi.",
      "error"
    );
  }

  /* ---------- Cadangan bila hasil gagal disimpan ke database ---------- */

  function renderFallback(data) {
    if (!fallbackBox) {
      return;
    }

    fallbackBox.innerHTML = "";
    fallbackBox.hidden = false;

    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h2");
    title.textContent = "Hasil analisis";
    card.appendChild(title);

    const warning = document.createElement("p");
    warning.className = "alert alert--warning";
    warning.textContent =
      data.warning || "Hasil tidak tersimpan, sehingga halaman detail tidak tersedia.";
    card.appendChild(warning);

    const prediction = document.createElement("p");
    const label = (data.prediction && data.prediction.label_display) ||
      (data.prediction && data.prediction.label) || "-";
    const confidence = data.prediction && typeof data.prediction.confidence === "number"
      ? Math.round(data.prediction.confidence * 1000) / 10
      : null;
    prediction.textContent = confidence === null
      ? "Kelas: " + label
      : "Kelas: " + label + " (" + confidence + "% keyakinan)";
    card.appendChild(prediction);

    if (Array.isArray(data.recommendations) && data.recommendations.length > 0) {
      const subtitle = document.createElement("h3");
      subtitle.textContent = "Rekomendasi";
      card.appendChild(subtitle);

      const list = document.createElement("ul");
      data.recommendations.forEach(function (item) {
        const li = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = item.title;
        li.appendChild(strong);
        const text = document.createElement("p");
        text.className = "muted small";
        text.textContent = item.message;
        li.appendChild(text);
        list.appendChild(li);
      });
      card.appendChild(list);
    }

    const disclaimer = document.createElement("p");
    disclaimer.className = "disclaimer";
    disclaimer.textContent = data.disclaimer || "";
    card.appendChild(disclaimer);

    fallbackBox.appendChild(card);
  }
})();
