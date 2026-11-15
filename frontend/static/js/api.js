/* ============================================================
   Pembungkus fetch() untuk seluruh komunikasi frontend -> backend.
   Semua error HTTP diubah menjadi Error JS yang seragam.
   ============================================================ */
(function () {
  "use strict";

  async function request(url, options) {
    let response;

    try {
      response = await fetch(url, options);
    } catch (networkError) {
      const error = new Error(
        "Tidak dapat terhubung ke server. Pastikan Flask sedang berjalan."
      );
      error.cause = networkError;
      throw error;
    }

    let payload = null;
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = null;
    }

    if (!response.ok) {
      const error = new Error(
        (payload && payload.message) || `Permintaan gagal (HTTP ${response.status}).`
      );
      error.status = response.status;
      error.errors = payload && payload.errors;
      error.payload = payload;
      throw error;
    }

    return payload;
  }

  window.SomnipathyApi = {
    postJSON(url, body) {
      return request(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(body),
      });
    },

    getJSON(url) {
      return request(url, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
    },
  };
})();
