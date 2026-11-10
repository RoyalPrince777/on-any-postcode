(() => {
  "use strict";
  const root = document.querySelector("[data-oware-root]");
  if (!root) return;

  const q = selector => root.querySelector(selector);
  const settings = q("#oware-settings");
  const csrf = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";
  const opening = {
    pits: JSON.parse(root.dataset.openingPits),
    players: [{name: "Player One", captured: 0}, {name: "Player Two", captured: 0}],
    legal_pits: [],
  };
  let state = null;
  let busy = false;

  function requestId() {
    return Array.from(crypto.getRandomValues(new Uint8Array(12)), byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function renderSettings() {
    const versusAgent = q("[data-mode]").value === "agent";
    q("[data-level-field]").hidden = !versusAgent;
    q("[data-player-two-field]").hidden = versusAgent;
    q("[data-settings-note]").hidden = state?.status !== "active";
    for (const control of q("[data-setup]").elements) {
      control.disabled = busy;
    }
    q("[data-settings-open]").disabled = busy;
  }

  function restoreSettings() {
    q("[data-setup]").reset();
    if (state?.started) {
      q("[data-variant]").value = state.variant;
      q("[data-mode]").value = state.agent_level ? "agent" : "local";
      if (state.agent_level) q("[data-level]").value = state.agent_level;
      q("[data-player-one]").value = state.players[0].name;
      if (!state.agent_level) q("[data-player-two]").value = state.players[1].name;
    }
    renderSettings();
  }

  function render(previousMove = null) {
    const active = state?.status === "active";
    renderSettings();
    q("[data-stop]").hidden = !active;
    q("[data-stop]").disabled = busy;
    if (!state?.started) {
      window.OAPOwareBoard.render(q("[data-board]"), opening, false);
      return;
    }

    q("[data-status]").textContent = state.variant === "nam-nam" ? "Nam-Nam" : "Abapa";
    const winner = state.players.find(player => player.id === state.winner_id);
    q("[data-turn]").textContent = active ? state.current_player_name + "’s turn" :
      state.status === "stopped" ? "Match stopped" : state.draw ? "Draw" : winner.name + " wins";
    const round = q("[data-round]");
    round.hidden = state.variant !== "nam-nam";
    round.textContent = round.hidden ? "" : "Round " + state.round;
    if (state.last_round) round.textContent += " · Previous round " + state.last_round.join("–");
    if (state.result === "round_replayed") round.textContent += " · Previous round replayed after a sowing loop";
    window.OAPOwareBoard.render(q("[data-board]"), state, !busy && active, 0, previousMove);

    const playerIndex = state.current_player_id === "p1" ? 0 : 1;
    const hasOpponentSeeds = state.pits.some((count, pit) => count && (state.owners?.[pit] ?? Math.floor(pit / 6)) !== playerIndex);
    let feedback = "";
    if (state.status === "completed") {
      feedback = {no_legal_move: "No legal moves left.", repetition: "Position repeated."}[state.result] || "";
    } else if (active && state.grand_slam_forfeited) {
      feedback = "Grand slam: sowing stands and the seeds stay in play.";
    } else if (active && !hasOpponentSeeds) {
      feedback = "Your opponent’s territory is empty. Choose a highlighted house to feed it.";
    }
    q("[data-feedback]").textContent = feedback;
  }

  async function action(path, payload) {
    if (busy) return false;
    busy = true;
    const error = q(settings.open ? "[data-settings-error]" : "[data-error]");
    error.textContent = "";
    render();
    const previous = state;
    let errorMessage;
    try {
      const options = payload ? {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-OAP-CSRF": csrf},
        body: JSON.stringify(payload),
      } : {};
      const response = await fetch("/arena/oware/" + path, {...options, cache: "no-store"});
      const result = await response.json();
      if (!response.ok) {
        errorMessage = result?.error?.message;
        throw new Error(result?.error?.code || "request_failed");
      }
      state = result;
      if (path === "state" || path === "start") {
        restoreSettings();
        if (settings.open) settings.close();
      }
    } catch (failure) {
      const messages = {
        oware_game_changed: "This match changed. Reload to see the current board.",
        oware_players_invalid: "Enter two different names.",
        oware_move_not_legal: "Choose a highlighted house in the current player’s territory.",
      };
      error.textContent = messages[failure.message] || errorMessage || "Oware could not update. Try again.";
    } finally {
      busy = false;
      render(path === "move" && state !== previous ? previous : null);
    }
  }

  q("[data-mode]").addEventListener("change", renderSettings);
  q("[data-settings-open]").addEventListener("click", () => {
    q("[data-settings-error]").textContent = "";
    restoreSettings();
    settings.showModal();
  });
  q("[data-settings-close]").addEventListener("click", () => settings.close());
  settings.addEventListener("close", restoreSettings);
  settings.addEventListener("cancel", event => {
    if (busy) event.preventDefault();
  });
  q("[data-setup]").addEventListener("submit", event => {
    event.preventDefault();
    if (busy || (!settings.open && state?.status === "active" && !window.confirm("End this match and start a new game?"))) return;
    const agent = q("[data-mode]").value === "agent";
    const first = q("[data-player-one]").value.trim() || "Player One";
    const second = agent ? (first.toLowerCase() === "oware agent" ? "Arena Agent" : "Oware Agent") :
      q("[data-player-two]").value.trim() || "Player Two";
    action("start", {variant: q("[data-variant]").value, players: [first, second], agent_level: agent ? q("[data-level]").value : null});
  });
  q("[data-board]").addEventListener("click", async event => {
    const button = event.target.closest("[data-pit]");
    if (!button || button.disabled) return;
    await action("move", {pit: Number(button.dataset.pit), request_id: requestId(), game_id: state.game_id});
    if (event.detail === 0) {
      (q("[data-pit]:enabled") || q("[data-start]")).focus();
    }
  });
  q("[data-stop]").addEventListener("click", () => action("stop", {request_id: requestId(), game_id: state.game_id}));
  action("state");
})();
