(() => {
  "use strict";

  const defaults = ["red", "blue", "green", "yellow"];
  const segment = [[1,6],[2,6],[3,6],[4,6],[5,6],[6,5],[6,4],[6,3],[6,2],[6,1],[6,0],[7,0],[8,0]];
  const rotate = ([x, y], seat) => seat ? rotate([14 - y, x], seat - 1) : [x, y];
  const track = defaults.flatMap((_, seat) => segment.map(point => rotate(point, seat)));
  const lanes = defaults.map((_, seat) => Array.from({length: 6}, (_, step) => rotate([step + 1, 7], seat)));
  const yard = [[1,1],[4,1],[1,4],[4,4]];
  const faces = ["🎲", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];

  function at(node, [x, y]) {
    node.style.gridColumnStart = x + 1;
    node.style.gridRowStart = y + 1;
    return node;
  }

  function tile(className, point, colour) {
    const node = at(document.createElement("span"), point);
    node.className = className;
    if (colour) node.dataset.counterColour = colour;
    node.setAttribute("aria-hidden", "true");
    return node;
  }

  function pieceButton(piece, player, colour, legal) {
    const button = document.createElement("button");
    const number = piece.id.split("-").at(-1);
    const zone = {yard:"Base", track:"Track " + (piece.track_square + 1), home:"Home lane " + piece.home_step}[piece.zone];
    button.type = "button";
    button.dataset.piece = piece.id;
    button.dataset.counterColour = colour;
    button.textContent = number;
    button.disabled = !legal;
    button.setAttribute("aria-label", player.name + ", piece " + number + ", " + zone);
    return button;
  }

  function mount(root) {
    const board = root.querySelector("[data-board]");
    const die = root.querySelector("[data-roll]");
    const face = root.querySelector("[data-die-face]");
    const rollValue = root.querySelector("[data-roll-value]");
    const legalChoices = root.querySelector("[data-legal]");
    const playersView = root.querySelector("[data-players-view]");
    const bases = defaults.map((_, seat) => tile("ludo-base", rotate([0, 0], seat).map(n => n === 14 ? 9 : n)));
    const squares = track.map(point => tile("ludo-square", point));
    const homeLanes = lanes.map(lane => lane.map(point => tile("ludo-square ludo-home", point)));
    const stacks = document.createElement("div");
    stacks.className = "ludo-stacks";
    board.prepend(...bases, ...squares, ...homeLanes.flat(), stacks);

    return function render(state, colours = defaults, canPlay = false) {
      const players = state.players || [];
      const legal = canPlay ? state.movable_piece_ids || [] : [];
      const rolled = state.pending_roll ?? state.last_roll;
      face.textContent = faces[rolled || 0];
      rollValue.textContent = rolled ?? "—";
      die.disabled = !canPlay || state.pending_roll != null;
      die.setAttribute("aria-label", rolled ? "Roll die. Last roll " + rolled : "Roll die");

      const safe = state.safe_track_squares || [0, 8, 13, 21, 26, 34, 39, 47];
      for (const [index, square] of squares.entries()) {
        square.textContent = safe.includes(index) ? "✦" : "";
        square.dataset.counterColour = index % 13 === 0 && players[index / 13] ? colours[index / 13] : "";
      }
      for (const [seat, base] of bases.entries()) {
        base.dataset.counterColour = players[seat] ? colours[seat] : "";
        for (const tile of homeLanes[seat]) tile.dataset.counterColour = base.dataset.counterColour;
      }

      const positions = new Map();
      const totals = [];
      const choices = [];
      for (const [seat, player] of players.entries()) {
        const total = document.createElement("span");
        total.dataset.counterColour = colours[seat];
        total.textContent = player.name + " " + player.finished + "/4";
        totals.push(total);
        for (const [index, piece] of player.pieces.entries()) {
          if (piece.zone === "finished") continue;
          const point = piece.zone === "yard" ? rotate(yard[index], seat) :
            piece.zone === "track" ? track[piece.track_square] : lanes[seat][piece.home_step - 1];
          const movable = legal.includes(piece.id);
          const key = point.join(",");
          if (!positions.has(key)) positions.set(key, at(document.createElement("div"), point));
          positions.get(key).append(pieceButton(piece, player, colours[seat], movable));
          if (movable) choices.push(pieceButton(piece, player, colours[seat], true));
        }
      }
      for (const stack of positions.values()) {
        stack.className = "ludo-stack";
        stack.classList.toggle("ludo-stack-many", stack.childElementCount > 1);
      }
      stacks.replaceChildren(...positions.values());
      playersView.replaceChildren(...totals);
      legalChoices.replaceChildren(...choices);
      legalChoices.hidden = choices.length === 0;
    };
  }

  window.OAPLudoBoard = {mount, defaults};
})();
