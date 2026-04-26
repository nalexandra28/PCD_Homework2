(function () {
  "use strict";

  var elInd = document.getElementById("conn-indicator");
  var elText = document.getElementById("conn-text");
  var elCount = document.getElementById("client-count");
  var elPopular = document.getElementById("popular-list");
  var elRecent = document.getElementById("recent-list");
  if (!elInd || !elText || !elCount || !elPopular || !elRecent) {
    return;
  }

  var MAX_BACKOFF_MS = 60 * 1000;
  var INITIAL_BACKOFF_MS = 1000;
  var GIVE_UP_AFTER = 0;

  var cfg = window.__DASHBOARD_CONFIG__;
  if (!cfg || !cfg.wsUrl) {
    elText.textContent = "Missing config (set window.__DASHBOARD_CONFIG__ in config.js)";
    elInd.setAttribute("data-state", "error");
    return;
  }

  var ws = null;
  var reconnectAttempt = 0;
  var reconnectTimer = null;
  var shouldRun = true;

  function setUi(state) {
    var map = {
      connected: { pill: "connected", text: "Connected" },
      reconnecting: { pill: "reconnecting", text: "Reconnecting" },
      offline: { pill: "offline", text: "Offline" },
      error: { pill: "error", text: "Error" }
    };
    var u = map[state] || map.offline;
    elInd.setAttribute("data-state", u.pill);
    elText.textContent = u.text;
  }

  function buildWsUrl() {
    var u;
    try {
      u = new URL(cfg.wsUrl, window.location.href);
    } catch (e) {
      throw new Error("Invalid wsUrl: " + cfg.wsUrl);
    }
    if (cfg.token) {
      u.searchParams.set("token", String(cfg.token));
    }
    return u.toString();
  }

  function jitteredBackoffMs(attempt) {
    var cap = Math.min(
      MAX_BACKOFF_MS,
      Math.floor(INITIAL_BACKOFF_MS * Math.pow(2, attempt - 1))
    );
    var v = 0.5 + Math.random() * 0.5;
    return Math.min(MAX_BACKOFF_MS, cap * v);
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  function renderEmptyPopular() {
    elPopular.innerHTML = "<li class=\"empty\">No data yet</li>";
  }

  function renderEmptyRecent() {
    elRecent.innerHTML = "<li class=\"empty\">No events yet</li>";
  }

  function applySnapshot(p) {
    if (typeof p.connectedClients === "number") {
      elCount.textContent = String(p.connectedClients);
    }
    var pop = p.popularMovies;
    if (Array.isArray(pop) && pop.length) {
      elPopular.innerHTML = pop
        .map(function (m) {
          var title = escapeHtml(String(m.movieTitle != null ? m.movieTitle : ""));
          var id = String(m.movieId != null ? m.movieId : "");
          var t = m.timestamp != null ? String(m.timestamp) : "";
          var vc = m.viewCount;
          return (
            "<li><strong>" +
            title +
            "</strong>" +
            (typeof vc === "number"
              ? " <span class=\"view-count\" aria-label=\"Views in time window\">(" +
                escapeHtml(String(vc)) +
                " in window)</span>"
              : "") +
            "<br /><span class=\"muted\">" +
            escapeHtml(id) +
            (t ? " · " + escapeHtml(t) : "") +
            "</span></li>"
          );
        })
        .join("");
    } else {
      renderEmptyPopular();
    }

    var rec = p.recentActions;
    if (Array.isArray(rec) && rec.length) {
      elRecent.innerHTML = rec
        .map(function (a) {
          var t = a.type != null ? String(a.type) : "event";
          var title = a.movieTitle != null ? String(a.movieTitle) : "";
          var mid = a.movieId != null ? String(a.movieId) : "";
          var at = a.at != null ? String(a.at) : "";
          return (
            "<li><strong>" +
            escapeHtml(t) +
            "</strong> — " +
            escapeHtml(title) +
            (mid ? " <span class=\"muted\">(" + escapeHtml(mid) + ")</span>" : "") +
            (at
              ? "<br /><small class=\"muted\">" + escapeHtml(at) + "</small>"
              : ""
            ) +
            "</li>"
          );
        })
        .join("");
    } else {
      renderEmptyRecent();
    }
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function onMessageText(txt) {
    var msg;
    try {
      msg = JSON.parse(txt);
    } catch (e) {
      return;
    }
    if (!msg || typeof msg.type !== "string") {
      return;
    }
    if (msg.type === "stats.snapshot") {
      applySnapshot(msg);
    }
  }

  function openSocket() {
    if (!shouldRun) {
      return;
    }
    var url = buildWsUrl();
    setUi("reconnecting");
    if (GIVE_UP_AFTER > 0 && reconnectAttempt > GIVE_UP_AFTER) {
      setUi("error");
      elText.textContent = "Stopped after " + GIVE_UP_AFTER + " failed attempts (reload to retry).";
      return;
    }
    if (GIVE_UP_AFTER > 0 && reconnectAttempt > 0) {
      elText.textContent = "Reconnecting (attempt " + reconnectAttempt + ")";
    }

    try {
      ws = new WebSocket(url);
    } catch (e) {
      scheduleReconnect();
      return;
    }

    ws.onopen = function () {
      reconnectAttempt = 0;
      setUi("connected");
    };
    ws.onmessage = function (ev) {
      if (typeof ev.data === "string") {
        onMessageText(ev.data);
      }
    };
    ws.onerror = function () {
      if (reconnectAttempt === 0) {
        setUi("reconnecting");
      }
    };
    ws.onclose = function () {
      ws = null;
      if (!shouldRun) {
        return;
      }
      setUi("reconnecting");
      scheduleReconnect();
    };
  }

  function scheduleReconnect() {
    if (!shouldRun) {
      return;
    }
    reconnectAttempt += 1;
    var delay = jitteredBackoffMs(reconnectAttempt);
    clearReconnectTimer();
    reconnectTimer = setTimeout(function () {
      openSocket();
    }, Math.floor(delay));
  }

  renderEmptyPopular();
  renderEmptyRecent();
  openSocket();
})();
