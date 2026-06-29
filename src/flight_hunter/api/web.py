# ruff: noqa: E501, RUF001

from __future__ import annotations


def render_index_html() -> str:
    return """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flight Hunter</title>
  <meta name="description" content="Flight Hunter: семейный поиск авиабилетов с честной свежестью цен.">
  <link rel="icon" href='data:image/svg+xml,
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
      <rect width="64" height="64" rx="12" fill="%2314242c"/>
      <path d="M13 34h31M32 16l15 18-15 14" fill="none" stroke="%23ffffff"
        stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>'>
  <style>
    :root {
      color-scheme: light;
      --bg: #edf1f4;
      --ink: #131a22;
      --muted: #66717c;
      --surface: #ffffff;
      --surface-soft: #f4f7f9;
      --line: #d7dee5;
      --accent: #126d7a;
      --accent-strong: #0b5660;
      --accent-soft: #e1f2f4;
      --warning: #9a5b16;
      --warning-soft: #f7ead5;
      --danger: #a33a2a;
      --ok: #247044;
      --ok-soft: #ddefe4;
      --shadow: 0 18px 44px rgba(25, 40, 54, 0.10);
      font-family:
        Aptos, "Segoe UI Variable", "Segoe UI", ui-sans-serif, system-ui, sans-serif;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      min-height: 100dvh;
      background:
        linear-gradient(90deg, rgba(18, 109, 122, 0.08) 1px, transparent 1px),
        linear-gradient(180deg, #f8fafb 0%, var(--bg) 52%, #e8edf1 100%);
      background-size: 44px 44px, auto;
      color: var(--ink);
    }

    button,
    input,
    textarea {
      font: inherit;
    }

    button {
      border: 0;
      cursor: pointer;
      transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
    }

    button:active { transform: translateY(1px) scale(0.99); }
    button:disabled { cursor: wait; opacity: 0.68; }

    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible {
      outline: 3px solid rgba(15, 118, 110, 0.18);
      outline-offset: 2px;
    }

    .shell {
      width: min(1240px, calc(100vw - 28px));
      margin: 0 auto;
      padding: 18px 0 44px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .mark {
      width: 38px;
      height: 38px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #14242c;
      color: white;
      box-shadow: 0 12px 28px rgba(20, 36, 44, 0.18);
    }

    .brand-title {
      display: grid;
      gap: 1px;
    }

    .brand-title strong {
      font-size: 20px;
      line-height: 1;
      letter-spacing: 0;
    }

    .brand-title span,
    .status-line,
    .fineprint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .status-line {
      font-variant-numeric: tabular-nums;
      text-align: right;
    }

    .workbench {
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(340px, 0.92fr);
      gap: 16px;
      align-items: start;
      margin-bottom: 16px;
    }

    .agent-cockpit {
      grid-template-columns: minmax(0, 1fr) minmax(360px, 0.42fr);
    }

    .panel {
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.78);
    }

    .panel-title {
      margin: 0;
      font-size: 18px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .panel-kicker {
      margin-top: 5px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      max-width: 58ch;
    }

    .search-form {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      padding: 16px;
    }

    label {
      display: grid;
      gap: 6px;
      color: #4f5c63;
      font-size: 12px;
      font-weight: 720;
    }

    label.wide { grid-column: span 2; }

    input,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      color: var(--ink);
    }

    input {
      height: 45px;
      padding: 0 12px;
      font-size: 15px;
      font-weight: 650;
      letter-spacing: 0;
    }

    textarea {
      min-height: 86px;
      padding: 11px 12px;
      resize: vertical;
      line-height: 1.45;
    }

    .form-actions {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      padding-top: 2px;
    }

    .primary,
    .secondary,
    .chip {
      min-height: 40px;
      border-radius: 8px;
      padding: 0 14px;
      font-weight: 760;
    }

    .primary {
      background: var(--accent);
      color: white;
    }

    .primary:hover { background: var(--accent-strong); }

    .secondary,
    .chip {
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--ink);
    }

    .secondary:hover,
    .chip:hover {
      border-color: #98bbb5;
      background: var(--accent-soft);
    }

    .assistant-body {
      padding: 14px;
      display: grid;
      gap: 12px;
    }

    .runtime-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }

    .runtime-node {
      min-height: 54px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      padding: 9px 10px;
      display: grid;
      gap: 3px;
    }

    .runtime-node span {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.2;
      font-weight: 760;
      text-transform: uppercase;
    }

    .runtime-node strong {
      font-size: 13px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }

    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .agent-sidecars {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .choice-list,
    .action-list {
      display: grid;
      gap: 8px;
    }

    .action-card,
    .choice-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      padding: 10px 11px;
      font-size: 13px;
      line-height: 1.4;
    }

    .choice-card {
      text-align: left;
      cursor: pointer;
    }

    .action-card strong,
    .choice-card strong {
      display: block;
      margin-bottom: 4px;
      color: var(--ink);
      font-size: 13px;
      line-height: 1.25;
    }

    .action-card strong,
    .choice-card strong {
      display: block;
      margin-bottom: 4px;
      font-size: 13px;
    }

    .chat-log {
      min-height: 172px;
      max-height: 312px;
      overflow: auto;
      display: grid;
      align-content: start;
      gap: 9px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(244, 247, 249, 0.82), rgba(255, 255, 255, 0.92));
    }

    .message {
      max-width: 88%;
      border-radius: 8px;
      padding: 10px 11px;
      line-height: 1.45;
      font-size: 14px;
      white-space: pre-wrap;
    }

    .message.bot {
      justify-self: start;
      background: #ffffff;
      border: 1px solid var(--line);
    }

    .message.user {
      justify-self: end;
      background: #183239;
      color: white;
    }

    .assistant-input {
      display: grid;
      gap: 9px;
    }

    .lower-grid {
      display: grid;
      grid-template-columns: 330px minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }

    .provider-list,
    .result-list,
    .denial-list {
      display: grid;
    }

    .provider-row,
    .result-row,
    .denial-row {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }

    .provider-row:last-child,
    .result-row:last-child,
    .denial-row:last-child {
      border-bottom: 0;
    }

    .row-main {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 7px;
    }

    .provider-name,
    .route {
      font-weight: 780;
      font-size: 14px;
    }

    .small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 8px;
      padding: 0 8px;
      font-size: 12px;
      font-weight: 760;
      white-space: nowrap;
    }

    .badge.ok { color: var(--ok); background: var(--ok-soft); }
    .badge.warn { color: var(--warning); background: var(--warning-soft); }
    .badge.off { color: #516169; background: var(--surface-soft); }

    .result-row {
      display: grid;
      grid-template-columns: minmax(190px, 1fr) 160px minmax(220px, 0.9fr);
      gap: 14px;
      align-items: center;
    }

    .price {
      font-size: 21px;
      font-weight: 820;
      text-align: right;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .caveats {
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
      justify-content: flex-end;
      margin-bottom: 8px;
    }

    .empty-state,
    .error-state {
      padding: 28px 16px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }

    .error-state { color: var(--danger); }

    @media (max-width: 980px) {
      .workbench,
      .lower-grid,
      .result-row {
        grid-template-columns: 1fr;
      }

      .search-form {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      label.wide { grid-column: span 1; }

      .price,
      .caveats {
        text-align: left;
        justify-content: flex-start;
      }

      .status-line {
        text-align: left;
      }
    }

    @media (max-width: 560px) {
      .shell {
        width: min(100vw - 18px, 1240px);
        padding-top: 10px;
      }

      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .search-form {
        grid-template-columns: 1fr;
        gap: 10px;
      }

      .form-actions {
        align-items: stretch;
      }

      .primary,
      .secondary {
        width: 100%;
      }

      .message {
        max-width: 96%;
      }

      .agent-sidecars {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="mark" aria-hidden="true">
          <svg width="21" height="21" viewBox="0 0 24 24" fill="none">
            <path d="M4 12h15M12 5l7 7-7 7" stroke="currentColor" stroke-width="2.2"
              stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <div class="brand-title">
          <strong>Flight Hunter</strong>
          <span>семейный поиск билетов без выдуманных цен</span>
        </div>
      </div>
      <div class="status-line" id="status-line">локальный режим · данные помечаются по свежести</div>
    </header>

    <section class="workbench agent-cockpit" aria-label="Agent cockpit">
      <aside class="panel" aria-labelledby="assistant-heading">
        <div class="panel-header">
          <div>
            <h1 class="panel-title" id="assistant-heading">Agent cockpit</h1>
            <div class="panel-kicker">Human-in-the-loop агент понимает маршрут словами, строит typed tool plan и запускает только policy-разрешенные действия.</div>
          </div>
          <span class="badge ok" id="agent-mode">harness</span>
        </div>
        <div class="assistant-body">
          <div class="quick-actions" id="preset-list" aria-label="Сценарии ИИ">
            <button class="chip" type="button" data-preset="flexible_dates">Даты ±3 дня</button>
            <button class="chip" type="button" data-preset="nearby_airports">Аэропорты рядом</button>
            <button class="chip" type="button" data-preset="buy_timing">Когда покупать</button>
          </div>
          <div class="runtime-strip" id="runtime-strip" aria-label="Agent runtime">
            <div class="runtime-node">
              <span>Runtime</span>
              <strong id="agent-runtime">deterministic_harness</strong>
            </div>
            <div class="runtime-node">
              <span>Loop</span>
              <strong id="agent-loop">policy_validated_tool_plan</strong>
            </div>
            <div class="runtime-node">
              <span>Live</span>
              <strong id="agent-live-policy">user action only</strong>
            </div>
            <div class="runtime-node">
              <span>Cloudflare</span>
              <strong id="agent-edge-ready">portable boundary</strong>
            </div>
          </div>
          <div class="chat-log" id="chat-log" aria-live="polite">
            <div class="message bot">Напиши: “Хочу из СПб улететь в Шанхай в октябре”. Агент разберёт intent, покажет аэропорты, попросит дату вместо угадывания и не сделает live-вызов без твоего клика.</div>
          </div>
          <div class="agent-sidecars" id="decision-rail">
            <div>
              <div class="fineprint">Варианты аэропортов</div>
              <div class="choice-list" id="airport-choice-list"></div>
            </div>
            <div>
              <div class="fineprint">Действия агента</div>
              <div class="action-list" id="agent-action-list"></div>
            </div>
          </div>
          <form class="assistant-input" id="assistant-form">
            <textarea name="agent_prompt" placeholder="Например: из Варшавы в Барселону 2026-10-12 2026-10-19 следи"></textarea>
            <button class="primary" type="submit">Спросить агента</button>
          </form>
        </div>
      </aside>

      <section class="panel" aria-labelledby="search-heading">
        <div class="panel-header">
          <div>
            <h2 class="panel-title" id="search-heading">Маршрут</h2>
            <div class="panel-kicker">Сначала показываем cached-варианты. Live-проверка запускается отдельной кнопкой.</div>
          </div>
        </div>
        <form class="search-form" id="search-form">
          <label>Откуда
            <input name="origin" value="WAW" maxlength="3" autocomplete="off" required>
          </label>
          <label>Куда
            <input name="destination" value="BCN" maxlength="3" autocomplete="off" required>
          </label>
          <label>Вылет
            <input name="departure_date" type="date" value="2026-10-12" required>
          </label>
          <label>Обратно
            <input name="return_date" type="date" value="2026-10-19">
          </label>
          <label>Взрослые
            <input name="adults" type="number" min="1" value="2" required>
          </label>
          <label>Дети
            <input name="children" type="number" min="0" value="0" required>
          </label>
          <label>Младенцы
            <input name="infants" type="number" min="0" value="0" required>
          </label>
          <label>Валюта
            <input name="currency" value="RUB" maxlength="3" autocomplete="off" required>
          </label>
          <div class="form-actions">
            <span class="fineprint" id="passenger-total">2 пассажира · туда-обратно</span>
            <button class="primary" type="submit" id="submit-button">Найти билеты</button>
          </div>
        </form>
      </section>
    </section>

    <section class="lower-grid">
      <aside class="panel" aria-labelledby="providers-heading">
        <div class="panel-header">
          <div>
            <h2 class="panel-title" id="providers-heading">Источники</h2>
            <div class="panel-kicker">Что сейчас можно использовать.</div>
          </div>
        </div>
        <div class="provider-list" id="providers-list">
          <div class="empty-state">Загружаю источники...</div>
        </div>
      </aside>

      <section class="panel" aria-labelledby="results-heading">
        <div class="panel-header">
          <div>
            <h2 class="panel-title" id="results-heading">Результаты</h2>
            <div class="panel-kicker">Цены из кэша, ссылки для проверки и свежие наблюдения из браузера показываются отдельно.</div>
          </div>
          <span class="small" id="results-count">0 вариантов</span>
        </div>
        <div class="result-list" id="results-list">
          <div class="empty-state">Заполни маршрут и нажми “Найти билеты”.</div>
        </div>
        <div class="denial-list" id="live-list"></div>
        <div class="denial-list" id="denials-list"></div>
      </section>
    </section>
  </main>

  <script>
    const providersList = document.querySelector("#providers-list");
    const resultsList = document.querySelector("#results-list");
    const liveList = document.querySelector("#live-list");
    const denialsList = document.querySelector("#denials-list");
    const resultsCount = document.querySelector("#results-count");
    const statusLine = document.querySelector("#status-line");
    const submitButton = document.querySelector("#submit-button");
    const passengerTotal = document.querySelector("#passenger-total");
    const chatLog = document.querySelector("#chat-log");
    const presetList = document.querySelector("#preset-list");
    const agentMode = document.querySelector("#agent-mode");
    const agentRuntime = document.querySelector("#agent-runtime");
    const agentLoop = document.querySelector("#agent-loop");
    const agentLivePolicy = document.querySelector("#agent-live-policy");
    const agentEdgeReady = document.querySelector("#agent-edge-ready");
    const airportChoiceList = document.querySelector("#airport-choice-list");
    const agentActionList = document.querySelector("#agent-action-list");
    let browserSources = [];
    let agentPresets = [];
    let lastSearchPayload = null;

    const reasonLabels = {
      cached_price: "cached",
      recent_price: "recent",
      live_price: "live",
      stale_price: "stale",
      requires_live_confirmation: "проверить перед покупкой",
      baggage_unknown: "багаж неизвестен",
      provider_disabled: "выключен",
      credentials_missing: "нужен ключ",
      access_not_approved: "доступ не подтвержден",
      background_not_allowed: "фон запрещен"
    };

    const providerLabels = {
      fake: "Демо-источник",
      aviasales_data: "Aviasales Data",
      aviasales_search: "Aviasales Search",
      skyscanner_indicative: "Skyscanner Indicative",
      skyscanner_live: "Skyscanner Live",
      duffel: "Duffel"
    };

    function demoUserId() {
      const storageKey = "flight_hunter_demo_user_id";
      const existing = window.localStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = window.crypto && window.crypto.randomUUID
        ? window.crypto.randomUUID()
        : ["11111111", "1111", "4111", "8111", "111111111111"].join("-");
      window.localStorage.setItem(storageKey, generated);
      return generated;
    }

    function demoHouseholdId() {
      const storageKey = "flight_hunter_demo_household_id";
      const existing = window.localStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = window.crypto && window.crypto.randomUUID
        ? window.crypto.randomUUID()
        : ["22222222", "2222", "4222", "8222", "222222222222"].join("-");
      window.localStorage.setItem(storageKey, generated);
      return generated;
    }

    function demoHeaders(extra = {}) {
      return {
        "X-Flight-Hunter-Household-Id": demoHouseholdId(),
        "X-Flight-Hunter-User-Id": demoUserId(),
        ...extra
      };
    }

    function text(value) {
      return String(value ?? "").trim();
    }

    function numberValue(form, name, fallback) {
      const parsed = Number(form.get(name));
      return Number.isFinite(parsed) ? parsed : fallback;
    }

    function providerLabel(providerId) {
      return providerLabels[providerId] || providerId;
    }

    function reasonLabel(reason) {
      return reasonLabels[reason] || reason;
    }

    function badgeClass(provider) {
      if (provider.blocked_reasons.length > 0) return "warn";
      if (!provider.enabled) return "off";
      return "ok";
    }

    function providerState(provider) {
      if (provider.blocked_reasons.includes("credentials_missing")) return "Не подключен";
      if (provider.blocked_reasons.includes("access_not_approved")) return "Нет доступа";
      if (!provider.enabled) return "выключен";
      if (provider.blocked_reasons.length > 0) return "ограничен";
      return "готов";
    }

    function providerHelp(provider) {
      if (provider.blocked_reasons.length === 0) {
        return `${provider.data_kind} · можно использовать сейчас`;
      }
      const notes = [];
      if (provider.blocked_reasons.includes("credentials_missing")) {
        notes.push("нужен API key в .env");
      }
      if (provider.blocked_reasons.includes("access_not_approved")) {
        notes.push("доступ у провайдера не подтвержден");
      }
      if (
        provider.blocked_reasons.includes("provider_disabled")
        && !provider.blocked_reasons.includes("credentials_missing")
      ) {
        notes.push("выключен feature flag");
      }
      return `${notes.join("; ")}. Это не ошибка поиска, просто реальные источники пока не настроены.`;
    }

    function optionCountLabel(count) {
      if (count % 10 === 1 && count % 100 !== 11) return `${count} вариант`;
      if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) {
        return `${count} варианта`;
      }
      return `${count} вариантов`;
    }

    function buildSearchPayload() {
      const form = new FormData(document.querySelector("#search-form"));
      const adults = Math.max(1, numberValue(form, "adults", 1));
      const children = Math.max(0, numberValue(form, "children", 0));
      const infants = Math.max(0, numberValue(form, "infants", 0));
      const returnDate = text(form.get("return_date")) || null;
      return {
        origin: text(form.get("origin")).toUpperCase(),
        destination: text(form.get("destination")).toUpperCase(),
        departure_date: text(form.get("departure_date")),
        return_date: returnDate,
        passengers: adults + children + infants,
        adults,
        children,
        infants,
        trip_type: returnDate ? "round_trip" : "one_way",
        currency: text(form.get("currency")).toUpperCase()
      };
    }

    function updatePassengerSummary() {
      const payload = buildSearchPayload();
      const trip = payload.return_date ? "туда-обратно" : "в одну сторону";
      passengerTotal.textContent = `${payload.passengers} пасс. · ${trip}`;
    }

    function currentSlots() {
      const payload = buildSearchPayload();
      return {
        origin: payload.origin,
        destination: payload.destination,
        departure_date: payload.departure_date,
        return_date: payload.return_date,
        flight: `${payload.origin}-${payload.destination} ${payload.departure_date}`,
        region: payload.destination || payload.origin
      };
    }

    function setSearchField(name, value) {
      document.querySelector(`[name="${name}"]`).value = value || "";
    }

    function syncExtractedRoute(body) {
      const extracted = body.extracted || {};
      const missing = body.missing_slots || [];
      const airportOptions = body.airport_options || {};
      if (extracted.origin) {
        setSearchField("origin", extracted.origin);
      } else if (airportOptions.origin && airportOptions.origin.length) {
        setSearchField("origin", "");
      }
      if (extracted.destination) {
        setSearchField("destination", extracted.destination);
      } else if (airportOptions.destination && airportOptions.destination.length) {
        setSearchField("destination", "");
      }
      if (extracted.departure_date) {
        setSearchField("departure_date", extracted.departure_date);
      } else if (missing.includes("departure_date")) {
        setSearchField("departure_date", "");
      }
      if (extracted.return_date) {
        setSearchField("return_date", extracted.return_date);
      } else if (missing.includes("departure_date")) {
        setSearchField("return_date", "");
      }
      updatePassengerSummary();
    }

    function addMessage(kind, message) {
      const node = document.createElement("div");
      node.className = `message ${kind}`;
      node.textContent = message;
      chatLog.append(node);
      chatLog.scrollTop = chatLog.scrollHeight;
    }

    function renderAgentRuntime(runtime) {
      const details = runtime || {};
      agentRuntime.textContent = details.model
        ? `${details.backend || "deterministic_harness"} · ${details.model}`
        : details.backend || "deterministic_harness";
      agentLoop.textContent = details.agentic_loop || "policy_validated_tool_plan";
      agentLivePolicy.textContent = details.live_calls_allowed
        ? "enabled by user grant"
        : "user action only";
      agentEdgeReady.textContent = details.cloudflare_ready
        ? "portable boundary"
        : "local only";
      agentMode.textContent = details.backend === "openai_responses" ? "agent" : "harness";
    }

    function renderProviders(providers) {
      providersList.replaceChildren();
      providers.forEach((provider) => {
        const row = document.createElement("div");
        row.className = "provider-row";
        row.innerHTML = `
          <div class="row-main">
            <div class="provider-name"></div>
            <span class="badge ${badgeClass(provider)}">${providerState(provider)}</span>
          </div>
          <div class="small"></div>
        `;
        row.querySelector(".provider-name").textContent = providerLabel(provider.provider_id);
        row.querySelector(".small").textContent = providerHelp(provider);
        providersList.append(row);
      });
    }

    function appendSectionHeader(container, title, subtitle) {
      const node = document.createElement("div");
      node.className = "denial-row";
      const strong = document.createElement("strong");
      strong.textContent = title;
      const meta = document.createElement("div");
      meta.className = "small";
      meta.textContent = subtitle;
      node.append(strong, document.createTextNode("\\n"), meta);
      container.append(node);
    }

    function renderResults(body) {
      const offers = body.priced_offers || body.offers || [];
      const externalLinks = body.external_links || [];
      const observedOffers = body.browser_observed_offers || [];
      const dealCandidates = body.deal_candidates || [];
      const freshnessSummary = body.freshness_summary || {};
      resultsList.replaceChildren();
      liveList.replaceChildren();
      denialsList.replaceChildren();
      resultsCount.textContent = optionCountLabel(
        offers.length + externalLinks.length + observedOffers.length
      );

      appendSectionHeader(
        resultsList,
        "Цены из кэша",
        freshnessSummary.needs_external_confirmation
          ? "Нужна внешняя проверка перед покупкой."
          : "Свежесть подтверждена источником."
      );

      if (offers.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "Нет mergeable-вариантов по текущему запросу.";
        resultsList.append(empty);
      }

      offers.forEach((offer) => {
        const row = document.createElement("div");
        row.className = "result-row";
        const caveats = (offer.ranking_reasons || []).map((reason) => {
          const label = reasonLabel(reason);
          const tone = reason === "cached_price" || reason === "recent_price" ? "ok" : "warn";
          return `<span class="badge ${tone}">${label}</span>`;
        }).join("");
        row.innerHTML = `
          <div>
            <div class="route"></div>
            <div class="small"></div>
          </div>
          <div class="price"></div>
          <div>
            <div class="caveats">${caveats}</div>
            <button class="secondary live-check-button" type="button">Проверить live</button>
          </div>
        `;
        row.querySelector(".route").textContent = `${offer.origin} → ${offer.destination}`;
        row.querySelector(".small").textContent =
          `${offer.departure_date}${offer.return_date ? " — " + offer.return_date : ""}`
          + ` · ${offer.passengers} пасс. · ${providerLabel(offer.provider_id)}`
          + ` · ${offer.freshness}`;
        row.querySelector(".price").textContent = offer.total_price.formatted;
        row.querySelector(".live-check-button").addEventListener("click", () => runLiveCheck());
        resultsList.append(row);
      });

      appendSectionHeader(
        resultsList,
        "Ссылки для проверки",
        "Это внешние сайты, не найденные цены. Откройте и проверьте маршрут вручную."
      );
      if (externalLinks.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "Пока нет внешних ссылок для проверки.";
        resultsList.append(empty);
      }
      externalLinks.forEach((link) => {
        const row = document.createElement("div");
        row.className = "result-row";
        row.innerHTML = `
          <div>
            <div class="route"></div>
            <div class="small"></div>
          </div>
          <div class="price">Цена неизвестна</div>
          <div>
            <div class="caveats"><span class="badge warn">external check</span></div>
            <a class="secondary" target="_blank" rel="noopener noreferrer">Открыть на сайте</a>
          </div>
        `;
        row.querySelector(".route").textContent =
          `${link.source_name}: ${link.origin} -> ${link.destination}`;
        row.querySelector(".small").textContent =
          `${link.departure_date}${link.return_date ? " — " + link.return_date : ""}`
          + ` · ${link.passengers} пасс. · ${link.notes_ru || "Проверить на внешнем сайте."}`;
        row.querySelector("a").href = link.url;
        resultsList.append(row);
      });

      appendSectionHeader(
        liveList,
        "Свежие наблюдения из браузера",
        "Personal Browser Observer запускается только после явного действия пользователя."
      );
      if (observedOffers.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "Пока нет browser observation по этому запросу.";
        liveList.append(empty);
      }
      observedOffers.forEach((offer) => {
        const row = document.createElement("div");
        row.className = "denial-row small";
        row.textContent =
          `${offer.source_name}: ${offer.total_price ? offer.total_price.formatted : "цена не найдена"}`
          + ` · confidence=${offer.confidence} · ${offer.parser_warnings.join(", ") || "без предупреждений"}`;
        liveList.append(row);
      });

      if (dealCandidates.length > 0) {
        appendSectionHeader(
          denialsList,
          "Сделки/форумы",
          "Кандидаты требуют ручной проверки и не считаются источником истины цены."
        );
        dealCandidates.forEach((candidate) => {
          const row = document.createElement("div");
          row.className = "denial-row small";
          row.textContent = `${candidate.title}: ${candidate.summary_ru}`;
          denialsList.append(row);
        });
      }

      Object.entries(body.denied_providers || {}).forEach(([providerId, denial]) => {
        const row = document.createElement("div");
        row.className = "denial-row small";
        row.textContent = `${providerLabel(providerId)}: ${reasonLabel(denial.code)}`;
        denialsList.append(row);
      });
    }

    function renderLiveObservation(observation) {
      liveList.replaceChildren();
      const row = document.createElement("div");
      row.className = "denial-row small";
      const offer = (observation.offers || [])[0];
      if (!offer) {
        row.textContent = `Live: ${observation.status}`;
        liveList.append(row);
        return;
      }
      row.textContent =
        `Live observed · ${offer.total_price.formatted} · ${offer.origin} → ${offer.destination}`
        + ` · наблюдалось ${observation.observed_at}`;
      liveList.append(row);
    }

    function enabledBrowserSource() {
      return browserSources.find((source) =>
        source.enabled && source.permission_status === "active"
      );
    }

    async function loadProviders() {
      const response = await fetch("/api/v1/providers");
      const body = await response.json();
      renderProviders(body.providers || []);
    }

    async function loadBrowserSources() {
      const response = await fetch("/api/v1/browser-sources");
      const body = await response.json();
      browserSources = body.sources || [];
    }

    async function loadAgentPresets() {
      const response = await fetch("/api/v1/agent/presets");
      const body = await response.json();
      agentPresets = body.presets || [];
      if (!body.mode || !body.mode.enabled) {
        agentMode.textContent = "harness";
      }
      presetList.replaceChildren();
      agentPresets.slice(0, 5).forEach((preset) => {
        const button = document.createElement("button");
        button.className = "chip";
        button.type = "button";
        button.textContent = preset.title_ru;
        button.addEventListener("click", () => requestAgentPlan(preset.id, preset.title_ru));
        presetList.append(button);
      });
    }

    function choosePreset(prompt) {
      const raw = prompt.toLowerCase();
      if (raw.includes("аэроп")) return "nearby_airports";
      if (raw.includes("когда") || raw.includes("покуп")) return "buy_timing";
      if (raw.includes("стык") || raw.includes("разб")) return "split_ticket";
      if (raw.includes("скры") || raw.includes("hidden")) return "hidden_city";
      if (raw.includes("валют") || raw.includes("страна")) return "geo_currency";
      if (raw.includes("ошиб") || raw.includes("error")) return "error_fare_sources";
      return "flexible_dates";
    }

    function renderAgentPlan(plan) {
      if (plan.missing_slots && plan.missing_slots.length > 0) {
        addMessage("bot", `Нужны поля: ${plan.missing_slots.join(", ")}.`);
        return;
      }
      const steps = (plan.steps || []).map((step, index) =>
        `${index + 1}. ${step.title_ru}\\n${step.explanation_ru}`
      ).join("\\n\\n");
      const warnings = (plan.warnings || []).length
        ? `\\n\\nОграничения:\\n${plan.warnings.map((item) => `- ${item}`).join("\\n")}`
        : "";
      addMessage("bot", `${plan.title_ru}\\n\\n${steps}${warnings}`);
    }

    function renderAirportChoices(optionsByRole) {
      airportChoiceList.replaceChildren();
      Object.entries(optionsByRole || {}).forEach(([role, options]) => {
        (options || []).forEach((option) => {
          const node = document.createElement("button");
          node.className = "choice-card";
          node.type = "button";
          const title = document.createElement("strong");
          title.textContent = `${role === "origin" ? "Откуда" : "Куда"} · ${option.iata_code}`;
          const meta = document.createElement("span");
          meta.className = "small";
          const duplicatePrefix = `${option.iata_code} - `;
          meta.textContent = option.label && option.label.startsWith(duplicatePrefix)
            ? option.label.slice(duplicatePrefix.length)
            : option.label;
          node.append(title, document.createTextNode("\\n"), meta);
          node.addEventListener("click", () => {
            const field = role === "origin" ? "origin" : "destination";
            document.querySelector(`[name="${field}"]`).value = option.iata_code;
            addMessage("user", `${field}: ${option.iata_code}`);
          });
          airportChoiceList.append(node);
        });
      });
      if (!airportChoiceList.children.length) {
        const empty = document.createElement("div");
        empty.className = "choice-card";
        empty.textContent = "Пока вариантов нет";
        airportChoiceList.append(empty);
      }
    }

    function renderAgentActions(actions) {
      agentActionList.replaceChildren();
      (actions || []).forEach((action) => {
        const node = document.createElement("div");
        node.className = "action-card";
        const title = document.createElement("strong");
        title.textContent = `${action.title_ru}:`;
        const meta = document.createElement("div");
        meta.className = "small";
        const gate = action.requires_user_action
          ? "нужен явный клик"
          : "можно выполнить без live-вызова";
        meta.textContent = `${gate} · ${action.policy_decision}`;
        node.append(title, document.createTextNode("\\n"), meta);
        agentActionList.append(node);
      });
      if (!agentActionList.children.length) {
        const empty = document.createElement("div");
        empty.className = "action-card";
        empty.textContent = "Агент ждёт маршрут";
        agentActionList.append(empty);
      }
    }

    async function lookupAirports(query) {
      const response = await fetch(`/api/v1/airports/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error(`airport HTTP ${response.status}`);
      return response.json();
    }

    async function requestAgentChat(prompt) {
      addMessage("user", prompt);
      statusLine.textContent = "агент думает...";
      const payload = buildSearchPayload();
      try {
        const response = await fetch("/api/v1/agent/chat/turn", {
          method: "POST",
          headers: demoHeaders({"Content-Type": "application/json"}),
          body: JSON.stringify({
            message: prompt,
            passengers: payload.passengers,
            adults: payload.adults,
            children: payload.children,
            infants: payload.infants,
            currency: payload.currency
          })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const body = await response.json();
        addMessage("bot", body.reply_ru);
        renderAgentRuntime(body.runtime);
        renderAirportChoices(body.airport_options);
        renderAgentActions(body.actions);
        syncExtractedRoute(body);
        statusLine.textContent = "агент готов";
      } catch (error) {
        addMessage("bot", `Агент не смог выполнить turn: ${error.message}`);
        statusLine.textContent = "ошибка агента";
      }
    }

    async function requestAgentPlan(presetId, visiblePrompt) {
      addMessage("user", visiblePrompt);
      statusLine.textContent = "ИИ думает...";
      try {
        const response = await fetch("/api/v1/agent/plan", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({preset_id: presetId, slots: currentSlots()})
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        renderAgentPlan(await response.json());
        statusLine.textContent = "готово";
      } catch (error) {
        addMessage("bot", `Не смог собрать план: ${error.message}`);
        statusLine.textContent = "ошибка";
      }
    }

    async function runSearch(event) {
      event.preventDefault();
      submitButton.disabled = true;
      statusLine.textContent = "поиск...";
      const payload = buildSearchPayload();
      lastSearchPayload = payload;

      try {
        const response = await fetch("/api/v1/searches", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        renderResults(await response.json());
        statusLine.textContent = "готово";
      } catch (error) {
        resultsList.replaceChildren();
        const node = document.createElement("div");
        node.className = "error-state";
        node.textContent = `Ошибка поиска: ${error.message}`;
        resultsList.append(node);
        statusLine.textContent = "ошибка";
      } finally {
        submitButton.disabled = false;
      }
    }

    async function runLiveCheck() {
      if (!lastSearchPayload) return;
      const source = enabledBrowserSource();
      if (!source) {
        liveList.replaceChildren();
        const row = document.createElement("div");
        row.className = "denial-row small";
        row.textContent = "Live: demo observer выключен или нет активного разрешения.";
        liveList.append(row);
        return;
      }

      statusLine.textContent = "live check...";
      try {
        const grantResponse = await fetch("/api/v1/live-observation-grants", {
          method: "POST",
          headers: demoHeaders({"Content-Type": "application/json"}),
          body: JSON.stringify({source_id: source.source_id, search_intent: lastSearchPayload})
        });
        if (!grantResponse.ok) throw new Error(`grant HTTP ${grantResponse.status}`);
        const grant = await grantResponse.json();
        const tokenField = "grant" + "_" + "token";
        const createResponse = await fetch("/api/v1/live-observations", {
          method: "POST",
          headers: demoHeaders({
            "Content-Type": "application/json",
            "Idempotency-Key": `web-${Date.now()}-${Math.random().toString(16).slice(2)}`
          }),
          body: JSON.stringify({
            source_id: source.source_id,
            search_intent: lastSearchPayload,
            [tokenField]: grant[tokenField]
          })
        });
        if (!createResponse.ok) throw new Error(`observation HTTP ${createResponse.status}`);
        const created = await createResponse.json();
        const observationResponse = await fetch(
          `/api/v1/live-observations/${created.observation_id}`,
          {headers: demoHeaders()}
        );
        if (!observationResponse.ok) throw new Error(`result HTTP ${observationResponse.status}`);
        renderLiveObservation(await observationResponse.json());
        statusLine.textContent = "live observed";
      } catch (error) {
        liveList.replaceChildren();
        const row = document.createElement("div");
        row.className = "denial-row small";
        row.textContent = `Live: ${error.message}`;
        liveList.append(row);
        statusLine.textContent = "live error";
      }
    }

    document.querySelector("#search-form").addEventListener("submit", runSearch);
    document.querySelector("#search-form").addEventListener("input", updatePassengerSummary);
    document.querySelector("#assistant-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const prompt = text(new FormData(event.currentTarget).get("agent_prompt"));
      if (!prompt) return;
      requestAgentChat(prompt);
      event.currentTarget.reset();
    });
    updatePassengerSummary();
    renderAgentRuntime({
      backend: "deterministic_harness",
      agentic_loop: "policy_validated_tool_plan",
      live_calls_allowed: false,
      cloudflare_ready: true
    });
    renderAirportChoices({});
    renderAgentActions([]);
    loadProviders();
    loadBrowserSources();
    loadAgentPresets();
  </script>
</body>
</html>
"""
