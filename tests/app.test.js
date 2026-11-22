/* Runs public/app.js against a stub DOM, so the URL building, snippet output and
   hash round trip are checked without a browser. Run: node tests/app.test.js */

const fs = require("fs");
const path = require("path");
const vm = require("vm");

let failures = 0;
function check(name, actual, expected) {
  const ok = typeof expected === "function" ? expected(actual) : actual === expected;
  if (!ok) {
    failures++;
    console.log("FAIL  " + name + "\n      got: " + JSON.stringify(actual));
  } else {
    console.log("ok    " + name);
  }
}

let metaPayload = { ok: true, user: "x", weeks: 52, source: "api", exact: true,
                    usable: true, busiest_week: 40, total: 1234 };

function makeDom(hash) {
  const byId = {};
  function el(tag) {
    const classes = new Set();
    const node = {
      tagName: tag, children: [], dataset: {}, style: {}, attributes: {},
      textContent: "", value: "", className: "", type: "", src: "", tabIndex: 0,
      offsetLeft: 0, offsetWidth: 100,
      classList: {
        add: (c) => classes.add(c),
        remove: (c) => classes.delete(c),
        toggle: (c, on) => (on ? classes.add(c) : classes.delete(c)),
        contains: (c) => classes.has(c)
      },
      setAttribute(k, v) { this.attributes[k] = String(v); },
      getAttribute(k) { return this.attributes[k]; },
      appendChild(c) { c.offsetLeft = this.children.length * 100; this.children.push(c); return c; },
      removeChild(c) { this.children = this.children.filter((x) => x !== c); },
      addEventListener() {}, focus() {}, select() {}, remove() {}
    };
    let id = "", html = "";
    Object.defineProperty(node, "id", {
      get() { return id; },
      set(v) { id = v; byId[v] = node; }
    });
    Object.defineProperty(node, "innerHTML", {
      get() { return html; },
      set(v) { html = v; }
    });
    return node;
  }

  const ids = ["preview", "status", "user", "themes", "accent", "accentHex",
               "accentClear", "riders", "sliders", "toggles", "tabs", "tabsWrap",
               "tabsActive", "snippet", "copy", "copyLabel", "hint", "frameWrap"];
  ids.forEach(function (i) { const n = el("div"); n.id = i; });

  let ready = null;
  const ctx = {
    console,
    document: {
      execCommand: () => true,
      getElementById: (i) => byId[i] || null,
      createElement: el,
      createTextNode: (t) => ({ nodeType: 3, textContent: t }),
      addEventListener: (ev, cb) => { if (ev === "DOMContentLoaded") ready = cb; },
      body: el("body")
    },
    location: { origin: "https://timeline.example", hash: hash || "" },
    history: { replaceState(_a, _b, url) { ctx.location.hash = url; } },
    navigator: {},
    fetch: () => Promise.resolve({ ok: metaPayload.ok !== false,
                                   json: () => Promise.resolve(metaPayload) }),
    Image: function () { this.src = ""; },
    requestAnimationFrame: (fn) => fn(),
    addEventListener() {},
    setTimeout, clearTimeout, encodeURIComponent, decodeURIComponent, Math, JSON, Intl
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "public", "app.js"), "utf8"), ctx);
  if (!ready) { throw new Error("app.js never registered DOMContentLoaded"); }
  ready();
  return { ctx, byId };
}

function previewUrl(byId) {
  // The preview is set through a preloading Image, so read the hash instead:
  // it carries exactly the query the URL is built from.
  return byId;
}

/* ---------- a fresh page ---------- */
let { ctx, byId } = makeDom("");
check("builds every theme swatch", byId.themes.children.length, 9);
check("builds every rider button", byId.riders.children.length, 5);
check("builds every slider", byId.sliders.children.length, 7);
check("builds every toggle", byId.toggles.children.length, 3);
check("builds every tab", byId.tabs.children.length, 4);
check("builds the clipped copy of the tab row", byId.tabsActive.children.length, 4);
check("the tab copy is out of the tab order", byId.tabsActive.children[0].tabIndex, -1);
check("no user means an empty query", ctx.location.hash, "#");
check("placeholder username in the snippet", byId.snippet.textContent,
      (s) => s.includes("your-username") && s.startsWith("[!["));
check("status invites a username", byId.status.textContent,
      (s) => s.toLowerCase().includes("sample"));

/* ---------- typing a username ---------- */
byId.user.value = "  octocat  ";
byId.user.oninput.call(byId.user);
check("username is trimmed into the query", ctx.location.hash, "#user=octocat");
check("markdown snippet links the profile", byId.snippet.textContent,
      "[![octocat's contribution wave](https://timeline.example/api/timeline?user=octocat)]"
      + "(https://github.com/octocat)");

/* ---------- changing a theme and a rider ---------- */
byId.themes.children[1].onclick();            // ice
byId.riders.children[1].onclick();            // sail
check("theme and rider reach the query", ctx.location.hash,
      "#user=octocat&theme=ice&rider=sail");

/* ---------- defaults stay out of the query ---------- */
byId.themes.children[0].onclick();            // back to ember, the default
byId.riders.children[0].onclick();            // back to surfer, the default
check("defaults are omitted", ctx.location.hash, "#user=octocat");

/* ---------- sliders ---------- */
const widthInput = byId["in-width"];
widthInput.value = "1200";
widthInput.oninput();
check("slider value reaches the query", ctx.location.hash, "#user=octocat&width=1200");
check("slider value is shown with its unit", byId["val-width"].textContent, "1200px");

/* ---------- toggles ---------- */
byId.toggles.children[0].onclick();           // sparkle off
check("a toggle off is sent as 0", ctx.location.hash, "#user=octocat&width=1200&glints=0");
byId.toggles.children[0].onclick();           // back on
check("a toggle back on disappears again", ctx.location.hash, "#user=octocat&width=1200");

/* ---------- custom accent ---------- */
byId.accentHex.value = "00aaff";
byId.accentHex.oninput.call(byId.accentHex);
check("accent is sent without the hash", ctx.location.hash,
      "#user=octocat&accent=00aaff&width=1200");
byId.accentHex.value = "nonsense";
byId.accentHex.oninput.call(byId.accentHex);
check("an unparseable accent is dropped", ctx.location.hash, "#user=octocat&width=1200");

/* ---------- the other tabs ---------- */
byId.tabs.children[1].onclick();
check("html snippet escapes its ampersands", byId.snippet.textContent,
      (s) => s.includes("&amp;width=1200") && !/[^&]&(?!amp;)/.test(s));
byId.tabs.children[2].onclick();
check("picture snippet offers a light source", byId.snippet.textContent,
      (s) => s.includes("prefers-color-scheme: light") && s.includes("theme=paper"));
byId.tabs.children[3].onclick();
const yaml = byId.snippet.textContent;
check("action snippet keeps github expressions literal", yaml,
      (s) => s.includes("${{ github.repository_owner }}") && s.includes("${{ secrets.GITHUB_TOKEN }}"));
check("action snippet carries the chosen settings", yaml, (s) => s.includes("width: 1200"));
check("action snippet omits defaults", yaml, (s) => !s.includes("theme: ember"));

/* ---------- the sliding tab highlight ---------- */
byId.tabs.offsetWidth = 400;                 // four 100px tabs
byId.tabs.children[1].onclick();
check("highlight clips to the chosen tab", byId.tabsActive.style.clipPath,
      "inset(0 200px 0 100px)");
byId.tabs.children[3].onclick();
check("highlight follows to the last tab", byId.tabsActive.style.clipPath,
      "inset(0 0px 0 300px)");

/* ---------- the copy button ---------- */
byId.copy.onclick();
check("copy blurs its label before swapping the word",
      byId.copy.classList.contains("swapping"), true);

/* ---------- a shared link ---------- */
const restored = makeDom("#user=torvalds&theme=matrix&rider=buoy&width=1000&glints=0");
check("hash restores the username", restored.byId.user.value, "torvalds");
// The builder emits a fixed order rather than echoing the input, so the same
// configuration always produces the same link however it was arrived at.
check("hash restores everything else, in canonical order", restored.ctx.location.hash,
      "#user=torvalds&theme=matrix&width=1000&rider=buoy&glints=0");
const reshuffled = makeDom("#glints=0&width=1000&rider=buoy&theme=matrix&user=torvalds");
check("a reshuffled link normalises to the same query",
      reshuffled.ctx.location.hash, restored.ctx.location.hash);
check("restored slider shows its value", restored.byId["val-width"].textContent, "1000px");

/* ---------- the status line, once the probe answers ---------- */
(async function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  metaPayload = { ok: true, user: "solo", weeks: 1, source: "public", exact: false,
                  usable: true, busiest_week: 1, total: 1 };
  const one = makeDom("");
  one.byId.user.value = "solo";
  one.byId.user.oninput.call(one.byId.user);
  await sleep(700);
  check("singular counts read correctly", one.byId.status.textContent,
        (s) => s.startsWith("1 week, 1 contribution,") && !s.includes("1 weeks"));
  check("the public route is named as approximate", one.byId.status.textContent,
        (s) => s.includes("levels only"));

  metaPayload = { ok: true, user: "many", weeks: 52, source: "api", exact: true,
                  usable: true, busiest_week: 40, total: 1234 };
  const many = makeDom("");
  many.byId.user.value = "many";
  many.byId.user.oninput.call(many.byId.user);
  await sleep(700);
  check("plural counts read correctly", many.byId.status.textContent,
        (s) => s.startsWith("52 weeks, 1234 contributions,") && s.includes("Exact"));

  console.log(failures ? `\n${failures} failing` : "\nall app.js checks passed");
  process.exit(failures ? 1 : 0);
})();
