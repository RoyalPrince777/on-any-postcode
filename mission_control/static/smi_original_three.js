/* Founder-only SMI Original Three bounded capability gateway.
   External same-origin script because the main OAP CSP forbids inline scripts. */
(() => {
  "use strict";
  const root = document.querySelector("[data-original-three-endpoint]");
  if (!root) return;
  const endpoint = root.dataset.originalThreeEndpoint;
  const csrf = root.dataset.originalThreeCsrf;
  if (!endpoint || !csrf) return;
  for (const form of root.querySelectorAll("[data-original-profile]")) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const profile = form.dataset.originalProfile;
      const output = root.querySelector('[data-original-result="' + profile + '"]');
      if (!output) return;
      const values = new FormData(form);
      let payload;
      if (profile === "m3gan") {
        payload = {
          request: values.get("request"),
          area: values.get("area"),
          consent: values.get("consent") === "on",
        };
      } else if (profile === "amelia") {
        payload = {
          action: values.get("action"),
          source_verified: values.get("source_verified") === "on",
        };
      } else if (profile === "black_box") {
        try {
          payload = {
            manifest: JSON.parse(values.get("manifest")),
            signature: values.get("signature"),
          };
        } catch {
          output.textContent = "Invalid JSON manifest. No operation performed.";
          return;
        }
      } else {
        output.textContent = "Unsupported profile. No operation performed.";
        return;
      }
      output.textContent = "Checking protected first-party policy…";
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-OAP-CSRF": csrf},
          body: JSON.stringify({profile, payload}),
        });
        const result = await response.json();
        output.textContent = JSON.stringify(result, null, 2);
      } catch {
        output.textContent = "The governed service did not respond. No operation confirmed.";
      }
    });
  }
})();
