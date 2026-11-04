"""Execute KORADASO omnibox behaviour in Node, without network or browser demos."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_koradaso_omnibox_runtime():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync(process.argv[1], "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "KORADASO browser inline script exists");

function submit(raw, externalSearch = false, approve = true) {
  const handlers = {};
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: "", checked: false, textContent: "",
      addEventListener: (event, callback) => { handlers[id + ":" + event] = callback; },
      querySelectorAll: () => [], append: () => {},
      setAttribute: () => {}
    });
    return elements.get(id);
  }
  const searchModes = [{value:"oap",checked:true,addEventListener:()=>{}},{value:"web",checked:false,addEventListener:()=>{}}];
  const visits = [];
  const prompts = [];
  const location = {
    origin: "https://onanypostcode.global", pathname: "/koradaso",
    assign: (url) => visits.push(url)
  };
  const window = {
    location, history: {length: 1},
    confirm: (message) => { prompts.push(message); return approve; }
  };
  const document = {
    referrer: "",
    getElementById: element,
    querySelectorAll: (selector) => selector === 'input[name="search-mode"]' ? searchModes : [],
    body: {classList: {toggle: () => {}, remove: () => {}}},
    createElement: () => ({append: () => {}, setAttribute: () => {}})
  };
  const localStorage = {getItem: () => null, setItem: () => {}, removeItem: () => {}};
  vm.runInNewContext(match[1], {window, document, localStorage, URL,
    console}, {timeout: 1500});
  element("address").value = raw;
  element("open-web-search").checked = externalSearch;
  searchModes.forEach(x => {x.checked = x.value === (externalSearch ? "web" : "oap");});
  assert.equal(typeof handlers["address-form:submit"], "function");
  handlers["address-form:submit"]({preventDefault: () => {}});
  return {visits, prompts, note: element("address-note").textContent};
}
assert.deepEqual(submit("KORADASO history").visits,
  ["/search?q=KORADASO%20history"]);
assert.deepEqual(submit("music").visits, ["/search?q=music"]);
assert.deepEqual(submit("/world").visits, ["/world"]);
assert.deepEqual(submit("/search").visits, ["/search"]);
assert.deepEqual(submit("/maps").visits, []);
assert.deepEqual(submit("/studio").visits, []);
assert.deepEqual(submit("/unknown").visits, []);
assert.deepEqual(submit("example.com").visits, ["https://example.com/"]);
assert.equal(submit("example.com", false, false).visits.length, 0);
assert.deepEqual(submit("music", true, true).visits,
  ["https://duckduckgo.com/?q=music"]);
assert.equal(submit("music", true, false).visits.length, 0);
assert.equal(submit("javascript://attack").visits.length, 0);
assert.equal(submit("//evil.example").visits.length, 0);
console.log("KORADASO omnibox: 13 runtime cases passed");
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "templates/koradaso_internet.html")],
        check=False, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
