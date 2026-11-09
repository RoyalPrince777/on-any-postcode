(() => {
  "use strict";

  const root = document.querySelector("[data-ludo-root]");
  if (!root) return;

  const q = selector => root.querySelector(selector);
  const csrf = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const renderBoard = window.OAPLudoBoard.mount(root);
  const settings = q("[data-settings]");
  const seats = [...root.querySelectorAll("[data-seat]")];
  const count = q("[data-count]");
  const error = q("[data-error]");
  let state;
  let busy = false;
  let matchColours;

  const configuredSeats = () => seats.slice(0, Number(count.value));
  const names = activeSeats => activeSeats.map(seat => seat.querySelector("[data-name]").value.trim());
  const colours = activeSeats => activeSeats.map(seat => seat.querySelector("[data-colour]").value);

  function updateSettings(locked) {
    const activeSeats = configuredSeats();
    const selected = colours(activeSeats);
    count.disabled = locked;
    for (const [index, seat] of seats.entries()) {
      seat.hidden = index >= activeSeats.length;
      seat.querySelector("[data-name]").disabled = locked;
      const picker = seat.querySelector("[data-colour]");
      picker.disabled = locked;
      for (const option of picker.options) {
        option.disabled = option.value !== picker.value && selected.includes(option.value);
      }
    }
  }

  function preview() {
    const activeSeats = configuredSeats();
    const palette = colours(activeSeats);
    const players = names(activeSeats).map((name, seat) => ({
      name: name || "Player " + (seat + 1),
      finished: 0,
      pieces: Array.from({length:4}, (_, index) => ({id:"p" + (seat + 1) + "-" + (index + 1), zone:"yard"})),
    }));
    renderBoard({players}, palette);
  }

  function render() {
    const active = state?.status === "active";
    updateSettings(busy || active);
    const start = q("[data-start]");
    start.disabled = busy || active;
    start.hidden = active;
    start.textContent = state ? "New game" : "Play";
    q("[data-stop]").disabled = busy || !active;
    q("[data-stop]").hidden = !active;
    if (!state) {
      preview();
      return;
    }
    q("[data-status]").textContent = state.status;
    q("[data-turn]").textContent = active ? state.current_player_name :
      state.status === "completed" ? state.winner_name + " wins" : "Match stopped";
    q("[data-feedback]").textContent = active
      ? state.pending_roll != null ? "Choose a highlighted piece." :
        state.last_roll != null ? "No legal move." : ""
      : state.status === "stopped" ? "Match stopped." : "";
    renderBoard(state, matchColours, !busy && active);
  }

  async function action(verb, payload, keyboard = false) {
    if (busy) return;
    busy = true;
    error.textContent = "";
    render();
    try {
      const response = await fetch("/arena/ludo/" + verb, {
        method:"POST", credentials:"same-origin", cache:"no-store",
        headers:{"Content-Type":"application/json", "X-OAP-CSRF":csrf},
        body:JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result?.error?.code);
      state = result;
      if (verb === "start") {
        matchColours = colours(configuredSeats());
        settings.open = false;
      }
    } catch (failure) {
      error.textContent = failure.message === "ludo_players_invalid"
        ? "Enter a different name for each player." : "The match could not update. Try again.";
    } finally {
      busy = false;
      render();
      if (keyboard) {
        const target = q("[data-legal] button:not([disabled])") ||
          q("[data-roll]:not([disabled])") || q("[data-start]:not([hidden])");
        target?.focus();
      }
    }
  }

  const requestId = () => crypto.randomUUID().replaceAll("-", "").slice(0,20);
  count.addEventListener("change", () => {
    const taken = new Set();
    for (const seat of configuredSeats()) {
      const picker = seat.querySelector("[data-colour]");
      if (taken.has(picker.value)) picker.value = [...picker.options].find(option => !taken.has(option.value)).value;
      taken.add(picker.value);
    }
  });
  settings.addEventListener("change", () => {
    updateSettings(busy || state?.status === "active");
    if (!state) preview();
  });
  q("[data-start]").onclick = () => {
    if (state?.status === "active") return;
    const activeSeats = configuredSeats();
    if (new Set(colours(activeSeats)).size !== activeSeats.length) {
      error.textContent = "Choose a different colour for each player.";
      settings.open = true;
      return;
    }
    action("start", {players:names(activeSeats)});
  };
  q("[data-roll]").onclick = event => action("roll", {request_id:requestId()}, event.detail === 0);
  root.addEventListener("click", event => {
    const button = event.target.closest("[data-piece]");
    if (button && !button.disabled) {
      action("move", {piece_id:button.dataset.piece, request_id:requestId()}, event.detail === 0);
    }
  });
  q("[data-stop]").onclick = () => action("stop", {request_id:requestId()});
  render();
})();
