/* Observable game activity, never predicted win odds. CommonJS for test runner. */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.OAPGameplayProgress = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const percent = (count, total) => Math.round(100 * count / total);
  function measure(game, state) {
    if (!state || typeof state !== "object") return null;
    if (game === "connect4") {
      if (!Array.isArray(state.board) || state.board.length !== 6 ||
          state.board.some(row => !Array.isArray(row) || row.length !== 7 ||
            row.some(cell => ![0, 1, 2].includes(cell)))) return null;
      const filled = state.board.flat().filter(cell => cell !== 0).length;
      return {value: percent(filled, 42), label: "Board occupied: " + filled + "/42"};
    }
    if (game === "oware") {
      if (!Array.isArray(state.players) || state.players.length !== 2 ||
          state.players.some(p => !Number.isInteger(p.captured) || p.captured < 0) ||
          !Array.isArray(state.pits) || state.pits.length !== 12 ||
          state.pits.some(n => !Number.isInteger(n) || n < 0)) return null;
      const captured = state.players.reduce((sum, p) => sum + p.captured, 0);
      if (captured + state.pits.reduce((sum, n) => sum + n, 0) !== 48) return null;
      return {value: percent(captured, 48), label: "Seeds captured: " + captured + "/48"};
    }
    if (game === "chess") {
      if (!state.board || typeof state.board !== "object" || Array.isArray(state.board)) return null;
      const pieces = Object.values(state.board);
      if (pieces.some(p => !/^[wb][KQRBNP]$/.test(p))) return null;
      const nonKings = pieces.filter(p => p[1] !== "K").length;
      if (pieces.filter(p => p === "wK").length !== 1 ||
          pieces.filter(p => p === "bK").length !== 1 || nonKings > 30) return null;
      return {value: percent(30 - nonKings, 30), label: "Pieces captured: " + (30 - nonKings) + "/30"};
    }
    return null;
  }
  return {measure};
});
