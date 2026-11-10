"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { measure } = require("../static/arena_gameplay_progress.js");

test("Connect 4 measures board occupancy rather than winning odds", () => {
  const board = Array.from({ length: 6 }, () => Array(7).fill(0));
  assert.deepEqual(measure("connect4", { board }), {value:0,label:"Board occupied: 0/42"});
  board[5][0] = 1;
  assert.deepEqual(measure("connect4", { board }), {value:2,label:"Board occupied: 1/42"});
  assert.equal(measure("connect4", { board: [[1]] }), null);
});

test("Oware Abapa measures captured seed proportion", () => {
  const base = { players: [{captured:0},{captured:0}], pits:Array(12).fill(4) };
  assert.deepEqual(measure("oware", base), {value:0,label:"Seeds captured: 0/48"});
  base.pits[0]=0;
  base.players[0].captured=4;
  assert.deepEqual(measure("oware", base), {value:8,label:"Seeds captured: 4/48"});
  base.players[0].captured=5;
  assert.equal(measure("oware", base), null);
});

test("Chess measures material removed, without treating it as game completion", () => {
  const board = { e1:"wK",e8:"bK" };
  for (let i=0;i<15;i++) {board["w"+i]="wP";board["b"+i]="bP";}
  assert.deepEqual(measure("chess", {board}), {value:0,label:"Pieces captured: 0/30"});
  delete board.w0;
  assert.deepEqual(measure("chess", {board}), {value:3,label:"Pieces captured: 1/30"});
  assert.equal(measure("chess", {board:{e1:"wK"}}), null);
});

test("Malformed states and unknown game types fail closed", () => {
  assert.equal(measure("connect4", null), null);
  assert.equal(measure("oware", {}), null);
  assert.equal(measure("chess", {board:{"e1":"wK","e8":"bK","x":"INVALID"}}), null);
  assert.equal(measure("unlisted", {}), null);
});
