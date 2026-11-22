/* timeline configurator.
   Keeps one state object, mirrors it into the preview URL, the snippets and the
   page hash, so a configuration can be shared as a link. */

(function () {
  "use strict";

  var DEFAULTS = {
    user: "", theme: "ember", accent: "",
    width: 880, height: 140, cell: 4, speed: 33, smooth: 1,
    weeks: 52, rider: "surfer", rider_at: 33,
    glints: true, dots: true, border: false
  };

  // Mirrors timeline/themes.py. Swatches show the background with the accent as a ring.
  var THEMES = [
    ["ember", "#FF6A3D", "#02070A"], ["ice", "#38BDF8", "#02070A"],
    ["matrix", "#22C55E", "#020A06"], ["grape", "#A855F7", "#07040E"],
    ["rose", "#F43F5E", "#0B0409"], ["gold", "#F59E0B", "#0A0702"],
    ["mono", "#94A3B8", "#05070A"], ["daylight", "#FF6A3D", "#FFFFFF"],
    ["paper", "#1F6FEB", "#F6F8FA"]
  ];

  var RIDERS = ["surfer", "sail", "buoy", "flag", "none"];

  var SLIDERS = [
    { key: "width", label: "Width", min: 320, max: 1600, step: 20, unit: "px" },
    { key: "height", label: "Height", min: 60, max: 400, step: 4, unit: "px" },
    { key: "cell", label: "Pixel size", min: 2, max: 10, step: 1, unit: "px" },
    { key: "speed", label: "Loop time", min: 6, max: 120, step: 1, unit: "s" },
    { key: "smooth", label: "Smoothing", min: 0.2, max: 5, step: 0.1, unit: "x" },
    { key: "weeks", label: "History", min: 8, max: 53, step: 1, unit: " weeks" },
    { key: "rider_at", label: "Rider position", min: 0, max: 100, step: 1, unit: "%" }
  ];

  var TOGGLES = [
    { key: "glints", label: "Sparkle" },
    { key: "dots", label: "Dot grid" },
    { key: "border", label: "Border" }
  ];

  var TABS = ["Markdown", "HTML", "Dark and light", "GitHub Action"];

  // "1 weeks" is the kind of small wrongness people notice without knowing why.
  var PLURAL = new Intl.PluralRules("en-US");
  function count(n, one, other) {
    return n + " " + (PLURAL.select(n) === "one" ? one : other);
  }

  var state = Object.assign({}, DEFAULTS);
  var activeTab = 0;
  var $ = function (id) { return document.getElementById(id); };

  /* ---------- state to query ---------- */

  function query(opts) {
    opts = opts || {};
    var parts = [];
    var push = function (k, v) { parts.push(k + "=" + encodeURIComponent(v)); };
    if (state.user && !opts.omitUser) push("user", state.user);
    var theme = opts.theme || state.theme;
    if (theme !== DEFAULTS.theme) push("theme", theme);
    if (state.accent) push("accent", state.accent.replace("#", ""));
    ["width", "height", "cell", "weeks", "rider_at"].forEach(function (k) {
      if (+state[k] !== DEFAULTS[k]) push(k, state[k]);
    });
    ["speed", "smooth"].forEach(function (k) {
      if (Math.abs(state[k] - DEFAULTS[k]) > 1e-9) push(k, state[k]);
    });
    if (state.rider !== DEFAULTS.rider) push("rider", state.rider);
    ["glints", "dots", "border"].forEach(function (k) {
      if (state[k] !== DEFAULTS[k]) push(k, state[k] ? 1 : 0);
    });
    return parts.join("&");
  }

  function imageUrl(opts) {
    var q = query(opts);
    return location.origin + "/api/timeline" + (q ? "?" + q : "");
  }

  /* ---------- preview ---------- */

  var previewTimer = null;

  function schedulePreview() {
    clearTimeout(previewTimer);
    $("frameWrap").classList.add("busy");
    previewTimer = setTimeout(drawPreview, 260);
  }

  // The pause buttons and a reduced-motion setting both ask the renderer for its still frame. Only the
  // preview gets it: the snippet keeps the moving wave.
  var calm = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var paused = false;
  function stillWanted() { return paused || calm.matches; }
  function withStill(url) { return stillWanted() ? url + (url.indexOf("?") < 0 ? "?" : "&") + "still=1" : url; }

  function setPaused(next) {
    paused = next;
    var buttons = document.querySelectorAll(".js-pause");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-pressed", paused ? "true" : "false");
      buttons[i].setAttribute("aria-label", paused ? "Play the wave" : "Pause the wave");
    }
    var hero = document.querySelector(".tl-wave img");
    if (hero) {
      var base = hero.getAttribute("data-src") || hero.getAttribute("src").replace(/&still=1$/, "");
      hero.setAttribute("data-src", base);
      hero.src = paused ? base + "&still=1" : base;
    }
    drawPreview();
  }

  function drawPreview() {
    var url = withStill(imageUrl());
    var probe = new Image();
    probe.onload = probe.onerror = function () {
      $("previewImg").src = url;
      $("frameWrap").classList.remove("busy");
    };
    probe.src = url;
  }

  /* ---------- username status ---------- */

  var metaTimer = null;

  function setStatus(text, kind) {
    var el = $("status");
    el.textContent = text;
    el.className = "cfg-status" + (kind ? " " + kind : "");
  }

  function scheduleMeta() {
    clearTimeout(metaTimer);
    if (!state.user) {
      setStatus("Showing a sample swell. Add a username to see your own.");
      return;
    }
    setStatus("Reading " + state.user + "'s calendar.");
    metaTimer = setTimeout(checkUser, 450);
  }

  function checkUser() {
    var who = state.user;
    fetch("/api/meta?user=" + encodeURIComponent(who) + "&weeks=" + state.weeks)
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, body: j }; }); })
      .then(function (res) {
        if (who !== state.user) { return; }
        if (!res.ok || !res.body.ok) {
          setStatus(res.body.error || "Could not read that calendar.", "warn");
          return;
        }
        var b = res.body;
        if (!b.usable) {
          setStatus(count(b.weeks, "week", "weeks")
            + " found, but too flat to make a wave. The stand-in swell is showing.", "warn");
          return;
        }
        setStatus(count(b.weeks, "week", "weeks") + ", "
          + count(b.total, "contribution", "contributions")
          + ", busiest week " + b.busiest_week + ". "
          + (b.exact ? "Exact daily counts." : "Public calendar, levels only."), "ok");
      })
      .catch(function () {
        if (who === state.user) { setStatus("Could not reach the renderer.", "warn"); }
      });
  }

  /* ---------- snippets ---------- */

  function snippet() {
    var who = state.user || "your-username";
    var alt = who + "'s contribution wave";
    var url = imageUrl();
    var profile = "https://github.com/" + who;

    if (activeTab === 0) {
      return "[![" + alt + "](" + url + ")](" + profile + ")";
    }
    if (activeTab === 1) {
      return '<a href="' + profile + '">\n'
        + '  <img src="' + url.replace(/&/g, "&amp;") + '" width="100%" alt="' + alt + '">\n'
        + "</a>";
    }
    if (activeTab === 2) {
      var light = imageUrl({ theme: "paper" }).replace(/&/g, "&amp;");
      var dark = url.replace(/&/g, "&amp;");
      return "<picture>\n"
        + '  <source media="(prefers-color-scheme: light)" srcset="' + light + '">\n'
        + '  <img src="' + dark + '" width="100%" alt="' + alt + '">\n'
        + "</picture>";
    }

    var withs = [["user", "\${{ github.repository_owner }}"], ["out", "assets/timeline.svg"]];
    if (state.theme !== DEFAULTS.theme) { withs.push(["theme", state.theme]); }
    if (state.accent) { withs.push(["accent", state.accent]); }
    ["width", "height", "cell", "weeks", "rider_at"].forEach(function (k) {
      if (+state[k] !== DEFAULTS[k]) { withs.push([k, state[k]]); }
    });
    ["speed", "smooth"].forEach(function (k) {
      if (Math.abs(state[k] - DEFAULTS[k]) > 1e-9) { withs.push([k, state[k]]); }
    });
    if (state.rider !== DEFAULTS.rider) { withs.push(["rider", state.rider]); }
    ["glints", "dots", "border"].forEach(function (k) {
      if (state[k] !== DEFAULTS[k]) { withs.push([k, state[k] ? "true" : "false"]); }
    });

    return "# .github/workflows/timeline.yml\n"
      + "name: timeline\n\n"
      + "on:\n"
      + '  schedule: [{ cron: "15 6 * * *" }]\n'
      + "  workflow_dispatch:\n\n"
      + "permissions:\n  contents: write\n\n"
      + "jobs:\n"
      + "  timeline:\n"
      + "    runs-on: ubuntu-latest\n"
      + "    steps:\n"
      + "      - uses: actions/checkout@v4\n"
      + "      - uses: PasinduSuraweera/timeline@v1\n"
      + "        with:\n"
      + withs.map(function (p) { return "          " + p[0] + ": " + p[1]; }).join("\n") + "\n"
      + "        env:\n"
      + "          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}\n"
      + "      - name: Commit the wave if it moved\n"
      + "        run: |\n"
      + "          git add -- assets/timeline.svg\n"
      + "          git diff --cached --quiet && exit 0\n"
      + '          git config user.name "github-actions[bot]"\n'
      + '          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"\n'
      + '          git commit -m "Update contribution wave"\n'
      + "          git push";
  }

  var HINTS = [
    "Paste this into your profile README. The image is generated per request, so it follows your calendar.",
    "Use this when you want to control the width, or wrap the wave in something else.",
    "GitHub serves the light version to readers browsing in light mode.",
    "No hosting needed: the Action renders the SVG into your repo and commits it when the shape changes."
  ];

  function renderOutput() {
    $("snippet").textContent = snippet();
    $("hint").textContent = HINTS[activeTab];
    Array.prototype.forEach.call($("tabs").children, function (b, i) {
      b.setAttribute("aria-selected", String(i === activeTab));
    });
    moveTabHighlight();
  }

  /* ---------- build the controls ---------- */

  function buildThemes() {
    var wrap = $("themes");
    THEMES.forEach(function (t) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "cfg-chip cfg-swatch";
      b.setAttribute("role", "radio");
      b.dataset.value = t[0];
      var dot = document.createElement("i");
      dot.style.background = t[2];
      dot.style.boxShadow = "inset 0 0 0 3px " + t[1];
      b.appendChild(dot);
      b.appendChild(document.createTextNode(t[0]));
      b.onclick = function () { state.theme = t[0]; sync(); };
      wrap.appendChild(b);
    });
  }

  function buildRiders() {
    var wrap = $("riders");
    RIDERS.forEach(function (name) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "cfg-chip";
      b.setAttribute("role", "radio");
      b.dataset.value = name;
      b.textContent = name;
      b.onclick = function () { state.rider = name; sync(); };
      wrap.appendChild(b);
    });
  }

  function buildSliders() {
    var wrap = $("sliders");
    SLIDERS.forEach(function (s) {
      var box = document.createElement("div");
      box.className = "cfg-slider";

      var head = document.createElement("div");
      head.className = "cfg-slider__head";
      var label = document.createElement("label");
      label.className = "cfg-label";
      label.htmlFor = "in-" + s.key;
      label.textContent = s.label;
      var value = document.createElement("span");
      value.className = "cfg-slider__val";
      value.id = "val-" + s.key;
      head.appendChild(label);
      head.appendChild(value);
      box.appendChild(head);

      var input = document.createElement("input");
      input.type = "range";
      input.min = s.min; input.max = s.max; input.step = s.step;
      input.id = "in-" + s.key;
      input.oninput = function () {
        state[s.key] = s.step < 1 ? parseFloat(input.value) : parseInt(input.value, 10);
        sync();
      };
      box.appendChild(input);
      wrap.appendChild(box);
    });
  }

  function buildToggles() {
    var wrap = $("toggles");
    TOGGLES.forEach(function (t) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "cfg-chip";
      b.dataset.value = t.key;
      b.textContent = t.label;
      b.onclick = function () { state[t.key] = !state[t.key]; sync(); };
      wrap.appendChild(b);
    });
  }

  function buildTabs() {
    var live = $("tabs");
    var clipped = $("tabsActive");
    TABS.forEach(function (name, i) {
      [live, clipped].forEach(function (row, isCopy) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "tab";
        b.textContent = name;
        if (isCopy) {
          b.tabIndex = -1;                 // the copy is decoration, not a control
          b.setAttribute("aria-hidden", "true");
        } else {
          b.setAttribute("role", "tab");
          b.onclick = function () { activeTab = i; renderOutput(); };
        }
        row.appendChild(b);
      });
    });
  }

  function moveTabHighlight() {
    var live = $("tabs");
    var btn = live.children[activeTab];
    if (!btn) { return; }
    // Measured against the clipped row itself: the live tablist may be narrower than the bar (the kit sizes a
    // tablist to its tabs), and a right inset taken from the narrower row lets the highlight run into the next tab.
    var rowWidth = $("tabsActive").offsetWidth || live.offsetWidth || 0;
    var left = btn.offsetLeft || 0;
    var right = Math.max(0, rowWidth - left - (btn.offsetWidth || 0));
    $("tabsActive").style.clipPath = "inset(0 " + right + "px 0 " + left + "px)";
  }

  /* ---------- keep everything in step ---------- */

  function sync(skipPreview) {
    Array.prototype.forEach.call($("themes").children, function (b) {
      b.setAttribute("aria-checked", String(b.dataset.value === state.theme));
    });
    Array.prototype.forEach.call($("riders").children, function (b) {
      b.setAttribute("aria-checked", String(b.dataset.value === state.rider));
    });
    Array.prototype.forEach.call($("toggles").children, function (b) {
      b.setAttribute("aria-pressed", String(!!state[b.dataset.value]));
    });
    SLIDERS.forEach(function (s) {
      $("in-" + s.key).value = state[s.key];
      var shown = s.step < 1 ? (+state[s.key]).toFixed(1) : state[s.key];
      $("val-" + s.key).textContent = shown + s.unit;
    });
    $("accentHex").value = state.accent || "";
    if (state.accent) { $("accent").value = state.accent; }

    renderOutput();
    writeHash();
    if (!skipPreview) { schedulePreview(); }
  }

  /* ---------- share the configuration in the address bar ---------- */

  function writeHash() {
    var q = query();
    var next = q ? "#" + q : "#";
    if (location.hash !== next) { history.replaceState(null, "", next); }
  }

  function readHash() {
    var raw = location.hash.replace(/^#/, "");
    if (!raw) { return; }
    raw.split("&").forEach(function (pair) {
      var i = pair.indexOf("=");
      if (i < 0) { return; }
      var k = decodeURIComponent(pair.slice(0, i));
      var v = decodeURIComponent(pair.slice(i + 1));
      if (!(k in DEFAULTS)) { return; }
      if (typeof DEFAULTS[k] === "boolean") { state[k] = v === "1" || v === "true"; }
      else if (typeof DEFAULTS[k] === "number") { state[k] = parseFloat(v) || DEFAULTS[k]; }
      else { state[k] = v; }
    });
    if (state.accent && state.accent.charAt(0) !== "#") { state.accent = "#" + state.accent; }
  }

  /* ---------- copy ---------- */

  function setCopyLabel(text, isDone) {
    var button = $("copy");
    button.classList.add("swapping");
    setTimeout(function () {
      $("copyLabel").textContent = text;
      button.classList.toggle("done", !!isDone);
      button.classList.remove("swapping");
    }, 120);
  }

  function copy() {
    var text = snippet();
    var done = function () {
      setCopyLabel("Copied", true);
      setTimeout(function () { setCopyLabel("Copy", false); }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else { fallback(); }

    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { /* nothing to do */ }
      document.body.removeChild(ta);
    }
  }

  /* ---------- go ---------- */

  function init() {
    buildThemes(); buildRiders(); buildSliders(); buildToggles(); buildTabs();

    $("user").oninput = function () {
      state.user = this.value.trim();
      sync();
      scheduleMeta();
    };
    $("accent").oninput = function () { state.accent = this.value; sync(); };
    $("accentHex").oninput = function () {
      var v = this.value.trim();
      state.accent = /^#?[0-9a-fA-F]{3}$|^#?[0-9a-fA-F]{6}$/.test(v)
        ? (v.charAt(0) === "#" ? v : "#" + v) : "";
      sync(true);
      schedulePreview();
    };
    $("accentClear").onclick = function () { state.accent = ""; sync(); };
    $("copy").onclick = copy;
    var pauses = document.querySelectorAll(".js-pause");
    for (var i = 0; i < pauses.length; i++) { pauses[i].onclick = function () { setPaused(!paused); }; }

    readHash();
    $("user").value = state.user;
    sync();
    scheduleMeta();

    // The highlight should be in place on first paint, not slide in from the edge.
    var tabs = $("tabsWrap");
    if (tabs) {
      tabs.classList.add("no-anim");
      moveTabHighlight();
      requestAnimationFrame(function () { tabs.classList.remove("no-anim"); });
    }
    window.addEventListener("resize", moveTabHighlight);
    // The tabs are measured in the web font; measure again once it has loaded, and whenever the row changes width
    // (the app stacks below 1024px), or the highlight sits a few pixels off its tab.
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(moveTabHighlight); }
    if (window.ResizeObserver) { new ResizeObserver(moveTabHighlight).observe($("tabs")); }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
