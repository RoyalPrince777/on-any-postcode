(() => {
  "use strict";

  function mount(root) {
    const board = root.querySelector("[data-board]");
    const controls = root.querySelector("[data-controls]");
    const cells = Array.from({length: 42}, (_, index) => {
      const cell = document.createElement("div");
      cell.className = "c4-cell";
      cell.style.setProperty("--c4-fall", -(Math.floor(index / 7) + 1) * 110 + "%");
      return cell;
    });
    const columns = Array.from({length: 7}, (_, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.column = index;
      button.setAttribute("aria-label", "Drop into column " + (index + 1));
      return button;
    });
    board.replaceChildren(...cells);
    controls.replaceChildren(...columns);

    return function render(rows, colours, locked) {
      columns.forEach((button, column) => {
        button.setAttribute("aria-disabled", String(locked || rows?.[0][column] !== 0));
      });
      board.setAttribute("aria-label", rows ? "Connect 4 board. Rows top to bottom: " +
        rows.map(row => row.map(piece => colours[piece]).join(", ")).join("; ") : "Empty Connect 4 board");
      const pieces = rows?.flat() || [];
      cells.forEach((cell, index) => {
        const piece = pieces[index] || 0;
        cell.dataset.counterColour = colours[piece];
        cell.classList.toggle("c4-p1", piece === 1);
        cell.classList.toggle("c4-p2", piece === 2);
      });
    };
  }

  window.OAPConnect4Board = {mount};
})();
