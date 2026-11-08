(() => {
  "use strict";

  function stonePile(count, className) {
    const pile = document.createElement("span");
    pile.className = className;
    pile.setAttribute("aria-hidden", "true");
    for (let index = 0; index < count; index++) pile.append(document.createElement("i"));
    return pile;
  }

  function render(board, state, enabled, bottomSeat = 0) {
    board.classList.add("oware-board");
    board.replaceChildren();
    if (!state.pits) return;

    for (const seat of [1 - bottomSeat, bottomSeat]) {
      const player = state.players[seat];
      const caption = document.createElement("div");
      caption.className = "oware-caption";
      caption.classList.toggle("oware-turn", state.status === "active" && state.current_player_id === player.id);
      const playerLabel = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = player.name;
      playerLabel.append(name);
      if (state.owners) {
        const territory = document.createElement("span");
        territory.className = "oware-territory";
        territory.textContent = state.owners.filter(owner => owner === seat).length + " houses";
        playerLabel.append(territory);
      }
      const store = document.createElement("div");
      store.className = "oware-store";
      const score = document.createElement("strong");
      score.className = "oware-score";
      score.textContent = player.captured;
      const scoreLabel = document.createElement("span");
      scoreLabel.textContent = "Captured";
      store.append(stonePile(player.captured, "oware-captured-stones"), scoreLabel, score);
      caption.append(playerLabel, store);

      const row = document.createElement("div");
      row.className = "oware-row";
      row.setAttribute("role", "group");
      row.setAttribute("aria-label", (seat === bottomSeat ? "Lower" : "Upper") + " houses");
      for (let offset = 0; offset < 6; offset++) {
        const house = seat === bottomSeat ? offset : 5 - offset;
        const pit = seat * 6 + house;
        const seeds = state.pits[pit];
        const button = document.createElement("button");
        button.type = "button";
        button.className = "oware-house";
        button.dataset.pit = String(pit);
        button.disabled = !enabled || !state.legal_pits.includes(pit);
        button.classList.toggle("oware-last", state.last_pit === pit);
        const owner = state.owners?.[pit] ?? seat;
        button.setAttribute("aria-label", "House " + (house + 1) + ", " + seeds + (seeds === 1 ? " seed" : " seeds") + ", owned by " + state.players[owner].name);

        const count = document.createElement("span");
        count.className = "oware-count";
        count.textContent = String(seeds);
        button.append(count, stonePile(seeds, "oware-stones"));
        if (owner !== seat) {
          const claim = document.createElement("span");
          claim.className = "oware-claim";
          claim.textContent = "P" + (owner + 1);
          claim.setAttribute("aria-hidden", "true");
          button.append(claim);
        }
        row.append(button);
      }
      if (seat === bottomSeat) board.append(row, caption);
      else board.append(caption, row);
    }
  }

  window.OAPOwareBoard = {render};
})();
