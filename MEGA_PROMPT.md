# MEGA PROMPT: построить Flight Hunter целиком

Скопируй весь этот файл в coding agent, работающий внутри пустого или подготовленного Git-репозитория. Файлы `AGENTS.md` и `docs/*` должны лежать рядом и считаются частью задания.

---

## РОЛЬ

Ты — principal software architect, staff backend engineer, senior frontend engineer, data engineer, SRE, security engineer, QA lead и product engineer в одном лице. Твоя задача — спроектировать и реализовать **завершённый production-grade продукт Flight Hunter**, а не прототип, tutorial, landing page, scaffold или MVP.

Работай автономно. Не останавливайся после первой работающей вертикали. Не проси пользователя выбирать стандартные библиотеки, имена таблиц или структуру каталогов, когда можешь принять разумное решение, записать ADR и продолжить. Задавай вопрос только при реальном внешнем блокере, который невозможно безопасно обойти конфигурацией; отсутствие API key не является блокером — используй feature flag, fixtures и deterministic fake provider.

Соблюдай `AGENTS.md`. Перед кодированием прочитай:

- `AGENTS.md`;
- `docs/PROVIDER_MATRIX.md`;
- `docs/ARCHITECTURE.md`;
- существующий код, migrations, CI и ADR;
- актуальную официальную документацию каждого провайдера, которого подключаешь.

Веди `IMPLEMENTATION_STATUS.md`: чек-лист обязательных этапов, решения, выполненные тесты, известные ограничения. Не помечай этап завершённым, пока его acceptance criteria реально не проходят.

---

# 1. ЦЕЛЬ ПРОДУКТА

Создай self-hosted, invitation-only приложение для владельца, супруги и друзей. Оно должно:

1. Искать авиабилеты по городам и аэропортам.
2. Работать с точными и гибкими датами.
3. Проверять соседние даты, по умолчанию ±3 дня.
4. Проверять близлежащие аэропорты в configurable радиусе, по умолчанию 150 км.
5. Показывать прямые рейсы, обычные пересадки, multi-city/open-jaw, one-way combinations и допустимые split-ticket/self-transfer комбинации.
6. Сравнивать не только цену, но и общее время, число пересадок, багаж, наземный трансфер, смену аэропорта, ночёвку, свежесть и риск.
7. Сохранять историю цены и строить графики.
8. Создавать watches и автоматически обновлять их только через источники, где background polling разрешён.
9. Отправлять Telegram alerts о существенном снижении, новом минимуме, выгодном направлении и подозрительно низкой цене.
10. Позволять live refresh по явному клику пользователя для user-initiated API.
11. Иметь полноценный responsive web UI/PWA и Telegram bot.
12. Иметь natural-language assistant, который понимает запросы, вызывает deterministic tools и объясняет результаты, но не выдумывает данные.
13. Поддерживать нескольких пользователей и households с изоляцией данных.
14. Разворачиваться одной понятной командой Docker Compose и иметь production runbooks.

Продукт не обязан продавать билет, принимать оплату или автоматически бронировать. Основной booking flow — прозрачный click-out/redirect по правилам провайдера. Архитектура может предусмотреть будущий booking module, но платежи и auto-booking не включать скрыто.

---

# 2. КЛЮЧЕВАЯ РЕАЛЬНОСТЬ ИСТОЧНИКОВ

Архитектура должна исходить из актуальных ограничений, а не из старых блогов.

## Aviasales Data API

- Используется как cached/indicative источник.
- Данные не считать real-time.
- Показывать freshness, observed time и необходимость live confirmation.
- Поддержать token из Travelpayouts.
- Реализовать как первый реальный provider adapter.
- Использовать server-side cache, rate limiter, retries и rate-limit headers.

## Aviasales Search API

- Доступен только проектам с подтверждёнными 50 000+ MAU.
- Старую версию, отключённую 15 июня 2026 года, не использовать.
- Adapter реализовать по новой спецификации, но выключить по умолчанию.
- Каждый вызов требует реального `UserActionGrant`.
- Никаких background calls.
- Никакого automated collection.
- Никакого объединения с API других авиаметапоисков.
- Результаты показывать в отдельном provider-isolated workspace.
- Booking link создавать только после пользовательского клика.

## Skyscanner

- API key только после партнёрского одобрения.
- Разделить Indicative и Live adapters.
- Live запускать только по user-generated запросу с точными датами.
- Indicative использовать для гибких дат только при разрешённой policy.
- Не использовать архивированный `skyscanner-python-sdk`.
- Предусмотреть официальный Skyscanner MCP как optional case-by-case integration, но не как обход доступа.

## Duffel

- Реализовать production adapter с test/live mode separation.
- Использовать Offer Requests и актуальные schemas.
- Учитывать expiry offers.
- Не считать background polling разрешённым без contract flag.
- Не включать booking/payment автоматически.

## Amadeus

- Не делать Self-Service стратегической зависимостью из-за объявленного закрытия соответствующего портала в июле 2026.
- Допускать legacy/Enterprise adapter только за feature flag и после проверки текущего доступа.

## Scraping

Не строить продукт на scraping. Запрещены CAPTCHA solving, stealth, fingerprint spoofing, rotating/residential proxies, подмена геолокации, обход login/paywall/access control и агрессивный polling. Playwright использовать для E2E собственного UI. Browser provider допускается только при явном разрешении и выключен по умолчанию.

---

# 3. ПРОДУКТОВЫЕ ПРИНЦИПЫ

1. **Никаких выдуманных рейсов и цен.** Каждое поле имеет provenance.
2. **Cached не равно live.** Это видно в карточке, графике и Telegram.
3. **Цена всегда контекстна.** Указывай пассажиров, валюту, cabin, baggage и тип маршрута.
4. **Provider policy исполняется кодом.** Документации недостаточно.
5. **LLM — интерфейс, не вычислитель.** Деньги, маршруты, policy, ranking и alerts детерминированы.
6. **Лучший вариант — многокритериальный.** Cheapest не всегда best.
7. **Не спамить.** Alerts используют hysteresis, cooldown и dedupe.
8. **Risk видим заранее.** Split/self-transfer/airport change/hidden-city не прячутся.
9. **Приватность по умолчанию.** Invitation-only, household isolation, минимизация данных.
10. **Работает без внешних ключей в demo mode**, но production adapters полностью реализованы и gated.

---

# 4. ОБЯЗАТЕЛЬНЫЙ ТЕХНИЧЕСКИЙ СТЕК

Проверь текущие stable/LTS версии в начале работы, зафиксируй ADR и pin versions. Базовая архитектура:

## Backend

- Python 3.13+;
- FastAPI;
- Pydantic v2;
- SQLAlchemy 2 async;
- Alembic;
- PostgreSQL + PostGIS;
- Redis;
- Dramatiq **или** Celery, выбрать один в ADR;
- HTTPX;
- structlog;
- OpenTelemetry;
- Prometheus metrics;
- aiogram 3;
- pytest, Hypothesis, respx, testcontainers.

## Frontend

- Next.js App Router;
- React + TypeScript strict;
- Tailwind;
- accessible component primitives;
- TanStack Query/Table;
- React Hook Form + Zod;
- ECharts/Recharts;
- Playwright E2E;
- Vitest/Testing Library;
- PWA.

## Tooling

- monorepo;
- uv для Python;
- pnpm workspace/Turborepo для JS;
- Docker Compose;
- Caddy;
- GitHub Actions;
- Ruff, mypy/pyright, ESLint, Prettier;
- pre-commit;
- secret/dependency/container scanning.

Не делай Kubernetes обязательным. Архитектура — модульный монолит с отдельными процессами web/api/worker/bot, а не микросервисный зоопарк.

---

# 5. ОБЯЗАТЕЛЬНАЯ СТРУКТУРА И АРХИТЕКТУРНЫЕ СЛОИ

Создай и соблюдай границы:

- `domain` — чистые value objects/entities/policies/calculations;
- `application` — use cases, ports, orchestration;
- `providers` — clients, DTO, mappings, policies, fixtures;
- `persistence` — repositories, SQLAlchemy, migrations;
- `geo` — аэропорты/PostGIS;
- `money` — FX/minor units/fees;
- `itinerary_engine` — граф и комбинации;
- `ranking` — Pareto/weighted score;
- `price_intelligence` — history/anomaly/buy-now;
- `notifications` — templates/dedupe/delivery;
- `policy` — provider policy guard;
- `llm` — provider-neutral structured tool layer;
- `api`, `worker`, `bot`, `web` — delivery/runtime.

Никакой бизнес-логики в FastAPI routes, React components или Telegram handlers. Provider-specific DTO не должен выходить за adapter boundary.

---

# 6. PROVIDER POLICY ENGINE — РЕАЛИЗОВАТЬ ПЕРВЫМ

Создай typed `ProviderPolicy` со следующими capability/constraint fields:

- provider id, policy version, official terms URL, verified date;
- enabled, credentials present, access approved;
- data kind: cached/indicative/live/bookable/feed;
- background allowed;
- user action required;
- merge allowed;
- raw persistence allowed;
- normalized persistence allowed;
- booking link requires click;
- booking link preload allowed;
- server-side only;
- real user IP required;
- request quotas;
- cache/result TTL;
- max concurrency;
- flexible dates/nearby/multi-city/baggage/fare-rules support.

Реализуй:

1. `ProviderPolicyRegistry`.
2. Versioned policy fixtures.
3. `PolicyGuard` перед каждым adapter call.
4. `QuotaReservationService`.
5. `UserActionGrant` — одноразовый, короткоживущий, привязан к пользователю, provider и fingerprint запроса.
6. Execution scopes:
   - `MERGEABLE`;
   - `PROVIDER_ISOLATED`;
   - `PRIVATE_TRANSIENT`.
7. Policy denial с machine-readable reason и понятным UI explanation.
8. Audit events для policy/credential/enable changes.

Добавь invariant tests, которые доказывают:

- worker не может вызвать provider с `background_allowed=false`;
- scheduler не может самостоятельно создать `UserActionGrant`;
- provider-isolated result не попадает в merged ranking;
- booking link не генерируется заранее, если запрещено;
- disabled/unapproved provider не вызывается.

---

# 7. КАНОНИЧЕСКАЯ ДОМЕННАЯ МОДЕЛЬ

Создай migrations, repositories, domain objects и API schemas минимум для следующих сущностей.

## Identity и sharing

- `users`;
- `households`;
- `household_memberships` с owner/admin/member/viewer;
- `invitations`;
- `sessions`/OIDC identities;
- `telegram_accounts`;
- `telegram_link_codes`;
- user preferences: locale, timezone, base currency, card FX fee, quiet hours, ranking preset.

## Reference data

- `airports` с PostGIS point, IATA/ICAO, type, active state, timezone, commercial relevance;
- `airport_aliases`;
- `metro_areas` и membership;
- `airlines`;
- `provider_locations`;
- `fx_rates`;
- `reference_data_imports`;
- admin overrides и provenance.

Импортируй OurAirports nightly/public-domain dataset через idempotent job. Не включай закрытые, военные и маленькие аэродромы в default autocomplete без фильтра. Поддержи manual correction.

## Search

- `search_intents`;
- `search_runs`;
- `provider_runs`;
- `user_action_grants`;
- `search_events` для SSE/progress;
- `search_result_sets` с merge scope;
- `search_run_errors`.

## Offers и itineraries

- `offers`;
- `offer_prices`;
- `fare_products`;
- `baggage_allowances`;
- `itineraries`;
- `slices`;
- `segments`;
- `seller_options`;
- `booking_action_descriptors`;
- `offer_provenance`;
- `normalization_warnings`;
- `raw_payload_refs` только при разрешении policy.

## Tracking

- `watches`;
- `watch_provider_configs`;
- `watch_runs`;
- `price_snapshots` append-only;
- `deal_scores`;
- `alerts`;
- `alert_state`;
- `notification_deliveries`;
- `notification_preferences`.

## Operations

- `provider_policies`/policy snapshots;
- `provider_credentials_metadata` без plaintext secret;
- `provider_health`;
- `quota_counters`;
- `job_runs`;
- `audit_log`;
- `data_exports`;
- `backup_records`.

## Обязательные value objects

- `Money(amount_minor: int, currency: ISO4217)`;
- `PassengerMix`;
- `DateFlexibility`;
- `LocationSet`;
- `SearchIntent`;
- `FlightSegment`;
- `ItineraryCandidate`;
- `OfferCandidate`;
- `Freshness`;
- `RiskAssessment`;
- `TotalTripCost`;
- `ProviderExecutionDecision`.

Правила:

- деньги никогда не float;
- все timestamps timezone-aware;
- хранить UTC и local timezone metadata;
- unknown не превращать в false/zero;
- immutable snapshots;
- multi-tenant queries всегда фильтруются household/user access;
- каждое предложение знает источник и время наблюдения;
- цена знает пассажирский состав;
- provider offer expiry отделён от historical snapshot.

---

# 8. SEARCH INTENT И NATURAL-LANGUAGE AGENT

## 8.1. Structured form

Пользователь может задать:

- origin: город, аэропорт, несколько аэропортов, «рядом со мной»;
- destination: конкретный, несколько, страна/регион, «куда угодно»;
- one-way/round-trip/multi-city;
- exact dates или ±N дней;
- stay length range;
- passengers с возрастами детей;
- cabin;
- carry-on/checked baggage;
- max stops;
- direct only;
- nearby radius для origin/destination;
- допустимость overnight, airport change, self-transfer;
- max total duration;
- departure/arrival time windows;
- preferred/excluded airlines/airports;
- budget и currency;
- ranking preset;
- provider selection;
- watch/notification thresholds.

## 8.2. Natural language

Примеры:

- «Из Варшавы или Кракова в Токио на 10–14 дней в октябре, плюс-минус три дня, один чемодан, максимум одна пересадка».
- «Куда дёшево из WAW в ноябре на неделю до 1500 PLN с человека».
- «Следи за Берлин — Бангкок 12–20 января и пиши, если упадёт ниже 2200 PLN».

LLM возвращает `SearchIntentDraft` только по JSON Schema. Затем deterministic validator:

- resolves locations через БД;
- проверяет date consistency;
- нормализует currency/passengers;
- отмечает ambiguity;
- не выдумывает IATA/airport/flight;
- создаёт UI/bot clarification только для действительно обязательного поля;
- имеет fallback parser без LLM для основных команд.

Создай tool interface минимум:

- `resolve_location`;
- `find_nearby_airports`;
- `build_date_matrix`;
- `estimate_search_budget`;
- `search_cached_provider`;
- `start_live_provider_search`;
- `get_search_progress`;
- `normalize_and_rank`;
- `compose_split_itineraries`;
- `get_price_history`;
- `create_watch`;
- `explain_provider_restriction`;
- `request_booking_action`.

LLM не вызывает provider напрямую: все tools идут через application service и policy guard.

Защити агент от prompt injection в названиях агентств, feed descriptions и provider text. External text всегда data, не instruction.

---

# 9. FLEXIBLE DATES И СОСЕДНИЕ АЭРОПОРТЫ

## 9.1. Date matrix

Для round trip ±3 дня есть до 49 комбинаций. Реализуй экономный planner:

1. Вычислить допустимые date pairs и stay length.
2. Получить cached/indicative matrix минимальным числом запросов.
3. Нормализовать цену на пассажирский состав.
4. Построить heatmap.
5. Выбрать top-N candidates с diversity по датам.
6. Не запускать автоматически live search для всех клеток.
7. Для live provider предложить пользователю refresh выбранной клетки.
8. Если provider contract явно допускает batch/automated запрос, всё равно соблюдать budget/quota.

Heatmap показывает:

- цену;
- freshness;
- direct/stops, если известно;
- лучший день;
- разницу с выбранными датами;
- недостаток данных отдельным состоянием.

## 9.2. Nearby airports

Используй PostGIS `ST_DWithin` и spatial index. Для каждого аэропорта:

- distance;
- metro relationship;
- commercial relevance;
- estimated ground time/cost;
- border crossing/unknown flag;
- operating hours unknown flag;
- source freshness.

Сравнение должно учитывать:

```text
effective_saving = airfare_saving
                 - added_ground_cost
                 - parking/rail/bus estimate
                 - optional time_value_penalty
                 - extra_risk_penalty
```

Не писать «экономия 300 PLN», если это только airfare difference; показывать gross и estimated net saving отдельно.

Пользователь может задать разные радиусы origin/destination и исключить конкретный airport.

---

# 10. PROVIDER ADAPTER CONTRACT

Каждый adapter реализует единый port, но только поддерживаемые capabilities:

```python
class FlightProvider(Protocol):
    async def search(self, request: ProviderSearchRequest, context: ProviderCallContext) -> ProviderSearchResult: ...
    async def poll(self, session: ProviderSession, context: ProviderCallContext) -> ProviderSearchResult: ...
    async def refresh_offer(self, offer_ref: ProviderOfferRef, context: ProviderCallContext) -> ProviderOfferResult: ...
    async def create_booking_action(self, offer_ref: ProviderOfferRef, context: UserClickContext) -> BookingAction: ...
    async def healthcheck(self) -> ProviderHealth: ...
```

Методы могут возвращать `UnsupportedCapability`, но не fake success.

Для каждого provider:

- официальный docs snapshot/date;
- typed request/response models;
- HTTP client;
- authentication;
- timeout;
- rate limiter;
- retry/backoff;
- circuit breaker;
- idempotency where supported;
- mapper;
- sanitized fixtures;
- contract tests;
- integration toggle;
- health/quota metrics;
- admin diagnostics;
- policy fixture;
- runbook.

Реализуй providers в таком порядке:

1. `FakeFlightProvider` — детерминированные сценарии для demo/E2E.
2. `OurAirportsImporter` и reference data.
3. `AviasalesDataProvider`.
4. `ManualOfferProvider` — пользователь может добавить проверенную ссылку/цену вручную.
5. `DealFeedProvider` — RSS/Atom/email webhook/manual feed, только разрешённые feeds.
6. `DuffelProvider` test mode, затем live gated.
7. `SkyscannerIndicativeProvider` gated.
8. `SkyscannerLiveProvider` user-action gated.
9. `AviasalesSearchProvider` provider-isolated, user-action gated, disabled by default.
10. Optional enterprise/direct adapters после полного core.

Ни один отсутствующий key не должен ломать startup.

---

# 11. НОРМАЛИЗАЦИЯ И ДЕДУПЛИКАЦИЯ

## 11.1. Canonical mapping

Нормализуй:

- origin/destination;
- local/UTC times;
- marketing/operating carrier;
- flight number;
- terminal;
- cabin/fare family;
- baggage;
- seller/agent;
- segment/slice order;
- total passenger price;
- taxes/fees when exposed;
- offer expiry;
- protected connection;
- booking action behavior;
- provider confidence/freshness.

Каждое canonical field хранит provenance или mapping source. Unknown field остаётся unknown.

## 11.2. Fingerprint

Stable fingerprint должен учитывать ordered segments, carriers, flight numbers, airports, local times, cabin, fare/baggage, seller и passenger mix. Предложения одинакового itinerary от разных продавцов группируются, но не схлопываются в одно.

## 11.3. Data quality

Создай validation/rejection reasons:

- impossible chronology;
- missing required airport/time;
- invalid currency;
- total mismatch;
- expired result;
- unsupported passenger mapping;
- provider schema drift;
- duplicate provider id conflict.

Rejected result виден в admin diagnostics и metrics, но не пользователю как билет.

---

# 12. ITINERARY ENGINE

## 12.1. Поддерживаемые типы

- direct;
- protected connection / single ticket;
- multi-city/open jaw;
- outbound/return from different one-way offers;
- split ticket;
- self-transfer;
- positioning leg;
- airport change;
- hidden-city research.

## 12.2. Graph search

Представь варианты как time-dependent graph. Edge — flight slice или ground transfer. Реализуй constrained beam search/k-shortest paths с budgets, а не полный перебор.

Constraints:

- chronological validity;
- minimum connection;
- self-transfer buffer;
- max stops;
- max duration;
- airport change allowed;
- overnight allowed;
- baggage recheck;
- provider/offer expiry;
- PNR grouping;
- visa/entry unknown;
- destination arrival deadline;
- origin departure window.

## 12.3. Split-ticket safety

Split result обязан показывать:

- отдельные bookings/PNR;
- что соединение не защищено;
- требование получить и снова сдать багаж;
- buffer;
- risk score;
- изменение airport/terminal;
- immigration/visa uncertainty;
- разные refund/change rules;
- сравнение с лучшим single-ticket.

Показывать split в default results только если:

- connection проходит conservative constraints;
- экономия остаётся материальной после ground/ancillary estimates;
- risk не выше пользовательского limit;
- все компоненты достаточно свежие;
- пользователь разрешил split/self-transfer.

## 12.4. Hidden-city

Реализуй отдельный experimental research mode:

- feature flag off by default;
- per-session acknowledgement;
- отдельная вкладка, не merged best ranking;
- high-risk badge;
- carry-on-only warning;
- предупреждение о checked baggage, отмене последующих сегментов, изменении маршрута и возможных последствиях по fare rules;
- никакого auto-booking;
- никаких обещаний;
- не предлагать для сложных/return itineraries без дополнительных строгих проверок;
- audit acknowledgement.

---

# 13. RANKING, TOTAL COST И RISK

## 13.1. Pareto first

Сначала вычисли Pareto frontier по цене, длительности, пересадкам, риску, baggage fit и freshness. Затем применяй configurable weighted score.

Presets:

- Cheapest;
- Best balance;
- Fastest;
- Lowest risk;
- Family;
- Checked baggage included.

## 13.2. Total trip cost

Отдельные компоненты:

- provider fare;
- baggage fee;
- other known ancillaries;
- card FX fee;
- provider currency conversion;
- estimated ground transfer;
- positioning flight;
- optional overnight stay;
- self-transfer contingency.

Каждая estimate имеет range/confidence/source. Не выдавай estimate за точную цену.

## 13.3. Risk model

Факторы:

- protected vs self-transfer;
- connection duration relative to conservative minimum;
- terminal/airport change;
- checked baggage;
- international border/visa unknown;
- overnight;
- separate tickets;
- provider freshness;
- offer expiry;
- schedule tightness;
- carrier change;
- historical reliability только если легально получены данные; иначе unknown.

Верни typed breakdown, а не один непрозрачный балл.

## 13.4. Explainability

Каждая карточка получает deterministic facts. LLM может перефразировать, но output проверяется против facts. Примеры:

- «дешевле на 14%, но два отдельных билета»;
- «экономия через соседний аэропорт 410 PLN до трансфера и около 220–300 PLN после оценки трансфера»;
- «cached price, замечена 3 часа назад»;
- «1 checked bag не подтверждён»;
- «время пересадки 2:10, для self-transfer рекомендованный буфер 3:00 — вариант скрыт default filter».

---

# 14. PRICE INTELLIGENCE

## 14.1. Price history

- Append-only snapshots.
- История по canonical itinerary group и broader route/date bucket.
- Сохраняй provider, observed_at, freshness, passenger mix, cabin, baggage, seller и search context.
- Не сравнивай несопоставимые цены.
- Графики: min/median, per-provider, per-airline, exact itinerary, normalized currency.
- Покажи gaps и отсутствие наблюдений.

## 14.2. Buy-or-wait / «когда покупать»

Не hardcode «покупай во вторник ночью». Реализуй evidence-based score:

- current percentile;
- median/MAD robust z-score;
- recent slope;
- volatility;
- days to departure;
- observation count;
- source freshness;
- cross-source agreement;
- known expiry/availability.

Statuses:

- `BUY_NOW_STRONG`;
- `BUY_NOW_WEAK`;
- `NEUTRAL`;
- `WAIT_WITH_RISK`;
- `INSUFFICIENT_DATA`.

Всегда показывай confidence и reasons. Добавь offline backtesting framework на historical snapshots. Не заявляй predictive accuracy без измерений.

## 14.3. Error-fare detector

Реализуй robust anomaly detection, учитывая:

- price/route historical median;
- MAD/z-score;
- comparable cabin/passengers/baggage;
- one-way vs return mismatch;
- currency sanity;
- impossible itinerary;
- missing mandatory fees;
- cross-market/cross-provider confirmation только если policy позволяет;
- freshness;
- live refresh по клику, если нужно.

Labels:

- `NORMAL`;
- `GOOD_DEAL`;
- `STRONG_DEAL`;
- `SUSPECTED_ANOMALY`;
- `LIKELY_DATA_ERROR`.

Telegram/web wording: «подозрение на аномально низкую цену», а не «гарантированный error fare». Напомни дождаться ticketing confirmation до невозвратных покупок.

## 14.4. Hot deals scanner

Пользователь задаёт:

- origin/nearby set;
- регионы/страны;
- travel windows;
- stay length;
- budget;
- cabin/baggage;
- max stops/risk;
- notification frequency.

Scanner работает только по background-allowed cached/indicative/feed sources. Он:

1. строит bounded candidate set;
2. использует popular/alternative directions;
3. получает матрицы;
4. сравнивает с историей;
5. ранжирует deals;
6. отправляет alert;
7. предлагает кнопку user-initiated live check.

Не выполняй бесконечный cartesian product городов/дат.

---

# 15. WATCHES, SCHEDULER И ALERTS

## 15.1. Watch lifecycle

- draft;
- active;
- paused;
- completed;
- expired;
- archived;
- blocked_by_provider_policy;
- needs_credentials.

Watch содержит immutable original intent и versioned current configuration.

## 15.2. Scheduler

Реализуй durable jobs с:

- idempotency;
- distributed locks;
- quota reservation;
- per-provider concurrency;
- adaptive intervals;
- jitter;
- exponential backoff;
- circuit breaker;
- deadlines;
- partial success;
- dead-letter queue;
- graceful shutdown;
- job admin screen.

Базовый interval только для background-allowed sources:

- >120 дней: 24ч;
- 61–120: 12ч;
- 15–60: 6ч;
- 3–14: 2ч;
- <3 дней: 1ч только при полезной freshness и достаточной quota.

Реальный interval = max(provider cache TTL, quota-based minimum, adaptive default). Не опрашивай cached source каждую минуту.

Для user-only live sources scheduler не делает search. Он может:

- сохранить watch;
- обновить cached signals;
- уведомить «есть существенное изменение, нажмите Проверить live»;
- после клика создать grant и запустить live flow.

## 15.3. Alert rules

Поддержи:

- ниже абсолютной цены;
- падение на X%;
- новый минимум;
- ниже historical percentile;
- strong deal/anomaly;
- появился direct flight;
- появился вариант с багажом;
- соседний аэропорт даёт net saving;
- лучший split вариант при допустимом risk;
- цена выросла перед deadline — optional warning.

## 15.4. Hysteresis, cooldown, dedupe

- material change threshold;
- per-watch cooldown;
- quiet hours;
- priority override для сильной аномалии;
- dedupe key;
- alert state machine;
- retry delivery без duplicate message;
- action «mute 24h», «pause watch», «mark irrelevant».

Сохраняй причину alert, baseline, current value, score inputs и rendered template version.

---

# 16. TELEGRAM BOT — ПОЛНОЦЕННЫЙ ИНТЕРФЕЙС

Используй aiogram 3.

## 16.1. Transport/security

- Production webhook over HTTPS.
- Проверяй `X-Telegram-Bot-Api-Secret-Token`.
- Deduplicate `update_id`.
- Long polling только development profile.
- Token не логируется.
- Callback data подписана/коротка и не содержит secrets.
- Telegram user id связывается с web account через одноразовый link code.
- Telegram username не является identity key.

## 16.2. Команды и flows

- `/start` — onboarding/link;
- `/search` — guided search;
- `/watch` — быстрый watch;
- `/watches` — список и действия;
- `/deals` — hot deals;
- `/pause`, `/resume`;
- `/settings`;
- `/help`.

Поддержи natural-language message после linking. Bot показывает parsed intent и просит подтвердить только существенные ambiguity.

Inline actions:

- открыть web result;
- проверить live;
- создать watch;
- сравнить даты;
- показать nearby airports;
- mute;
- pause;
- изменить threshold;
- отметить нерелевантным.

## 16.3. Message design

Краткое сообщение содержит:

- маршрут;
- total price и пассажиров;
- relative saving;
- даты;
- stops/duration;
- baggage status;
- source/freshness;
- risk label;
- 2–3 кнопки.

Long details открываются в web UI. Поддержи RU/EN локализацию и timezone пользователя.

## 16.4. Booking click rules

Если provider требует click-gated link, Telegram button сначала вызывает backend action endpoint, проверяющий user click context, и только затем получает redirect. Не embed заранее сгенерированный link в alert.

---

# 17. WEB UI / PWA

Создай polished, responsive интерфейс без шаблонного admin-dashboard вида.

## 17.1. Auth/onboarding

- invitation-only;
- owner bootstrap;
- sign-in;
- household creation/invite;
- locale/timezone/currency;
- Telegram linking;
- demo walkthrough.

Поддержи безопасный password auth или OIDC/magic link; решение запиши ADR. Если passwords — Argon2id, secure sessions, CSRF protection.

## 17.2. Dashboard

- active watches;
- price changes;
- current best deals;
- upcoming trips/searches;
- alert activity;
- provider freshness/health summary;
- clear empty states.

## 17.3. Search workspace

- natural language box + structured form;
- autosuggest city/airport;
- multi-origin/multi-destination;
- date picker with flexibility;
- trip length;
- passenger/baggage/cabin;
- nearby radius;
- risk controls;
- provider selector;
- estimated query plan/cost;
- explain why provider is unavailable or user-only.

Search results stream via SSE:

- progress by provider;
- partial results;
- cancelled/failed providers;
- no fake loading percentages.

## 17.4. Results

Views:

- Best;
- Cheapest;
- Fastest;
- Lowest risk;
- Direct;
- Split/self-transfer;
- provider-isolated tabs;
- date heatmap;
- nearby-airport comparison.

Card fields:

- total price/passengers;
- normalized and provider currency;
- duration/stops;
- segment timeline;
- seller/airline;
- baggage/fare family;
- freshness;
- risk;
- total-cost assumptions;
- explanation;
- compare/watch/booking actions.

Реализуй compare drawer/table до 4 вариантов.

## 17.5. Watch detail

- current best;
- history chart;
- min/median;
- alert timeline;
- provider run history;
- scheduler next run;
- thresholds;
- pause/resume/archive;
- change version history;
- Telegram destinations.

## 17.6. Deals

- feed/cards;
- confidence;
- origin/region/date/budget filters;
- gross/net saving;
- anomaly warnings;
- button live check.

## 17.7. Settings/admin

User:

- profile;
- locale/timezone/currency;
- FX fee;
- quiet hours;
- ranking defaults;
- Telegram;
- privacy export/delete.

Admin:

- invitations/users/households;
- provider enable/access/credentials metadata;
- policy version and docs verification date;
- quotas/circuit breaker/health;
- jobs/dead letters;
- airport imports;
- audit log;
- backups;
- demo/fake scenarios.

## 17.8. Accessibility/i18n

- WCAG AA baseline;
- keyboard navigation;
- visible focus;
- semantic tables/forms;
- screen-reader labels;
- reduced motion;
- dark/light;
- RU/EN complete, architecture ready for PL;
- no raw untranslated keys.

---

# 18. API И REAL-TIME PROGRESS

Создай versioned REST API и OpenAPI-generated frontend client.

Минимальные groups:

- auth/invitations/sessions;
- users/households/preferences;
- Telegram linking/webhook;
- airports/autocomplete/nearby;
- searches/events/live-refresh/cancel;
- offers/compare/booking-action;
- watches/history/actions;
- deals;
- providers/policies/health;
- admin/jobs/imports/audit/backups;
- privacy export/delete.

Требования:

- typed error envelope;
- request/correlation ids;
- idempotency keys для важных POST;
- pagination/filter/sort;
- optimistic concurrency/version field для watch updates;
- SSE с reconnect/last-event-id;
- authz на каждом resource;
- rate limits;
- OpenAPI examples без secrets;
- API contract tests.

---

# 19. FX, ВАЛЮТА И «ДРУГОЙ РЫНОК»

Реализуй корректное сравнение валют:

- provider amount/currency сохраняются неизменными;
- normalized currency per user;
- FX rate и timestamp;
- decimal arithmetic;
- card foreign transaction fee;
- stale FX label;
- unsupported currency handling.

Market/country comparison разрешено только через официальные provider parameters и в пределах договора. Не меняй IP, timezone, geolocation или browser fingerprint, чтобы притвориться пользователем другой страны.

Для одинакового itinerary показывай:

- quoted market/currency;
- converted amount;
- estimated card fee;
- final comparable amount;
- data freshness;
- caveat, что seller/availability могут отличаться.

---

# 20. SECURITY, PRIVACY, COMPLIANCE

Реализуй и документируй:

- threat model;
- invitation-only auth;
- secure cookies/session rotation;
- CSRF;
- RBAC;
- household isolation tests;
- secret manager/env integration;
- encryption at rest для provider secrets;
- outbound host allowlist;
- SSRF protection;
- request timeout/body limits;
- webhook signatures/secrets;
- audit log;
- admin step-up confirmation для опасных действий;
- log redaction;
- raw payload retention;
- privacy export/delete;
- backup encryption;
- dependency/secret/container scans;
- Content Security Policy;
- secure headers;
- non-root containers;
- least privilege DB users where practical.

Никакого хранения card data. Booking redirects считаются untrusted external URLs и проходят allowlist/validation по provider contract.

---

# 21. OBSERVABILITY И OPERATIONS

## Metrics

- HTTP latency/error;
- search latency/provider;
- provider 429/auth/schema errors;
- rate-limit remaining;
- cache hit ratio;
- provider circuit state;
- normalization reject count;
- scheduler lag;
- watch last-success age;
- queue depth/dead letters;
- alerts generated/deduped;
- Telegram delivery;
- DB pool;
- SSE connections.

## Logging

Structured JSON с correlation/search/provider/job ids. Redact secrets, IP where not operationally needed, booking links и PII.

## Tracing

Web/Telegram action → API → planner → adapter → normalize → rank → persist → notify.

## Health

- `/health/live`;
- `/health/ready`;
- dependency health;
- provider diagnostic отдельно и не блокирует readiness всего приложения, если optional provider unavailable.

## Runbooks

Создай минимум:

- install/update;
- add/rotate provider credential;
- 429/circuit breaker;
- provider schema drift;
- Telegram webhook failure;
- queue backlog;
- airport import failure;
- backup/restore;
- database migration failure;
- secret leak response;
- disable compromised provider;
- data export/delete.

---

# 22. ТЕСТОВАЯ СТРАТЕГИЯ

## 22.1. Unit tests

Покрой:

- Money/minor units/rounding;
- FX and fees;
- timezone/DST;
- flexible-date expansion;
- nearby airport filtering;
- search budget;
- provider policy decisions;
- UserActionGrant lifecycle;
- canonical mapping;
- dedupe/fingerprint;
- itinerary chronology;
- connection buffers;
- split-ticket constraints;
- hidden-city gating;
- risk breakdown;
- Pareto/weighted ranking;
- total-cost estimates;
- price percentile/MAD/anomaly;
- watch interval;
- alert hysteresis/dedupe;
- localization formatting.

## 22.2. Property-based tests

Минимальные properties:

- Money operations сохраняют currency и minor-unit integrity;
- itinerary никогда не прибывает раньше вылета в UTC;
- connection path монотонен по времени;
- forbidden provider mode никогда не проходит guard;
- provider-isolated set не появляется в merged result;
- fingerprints стабильны при перестановке provider response fields;
- ranker не выдаёт NaN/Infinity на unknown fields;
- alert retries не создают второй logical delivery;
- date matrix не выходит за requested bounds;
- household isolation не зависит от client-provided user id.

## 22.3. Contract tests

Для каждого adapter:

- success;
- empty result;
- partial result;
- 400/401/403/404;
- 429 с retry/reset;
- 5xx;
- timeout;
- malformed JSON;
- unknown extra fields;
- missing required field;
- expired offer;
- currency edge;
- provider schema fixture version.

CI не обращается к live providers. Отдельный manual/secure smoke workflow может использовать test environment credentials.

## 22.4. Integration tests

С testcontainers:

- Postgres/PostGIS;
- Redis;
- migrations;
- outbox/job processing;
- distributed locks;
- SSE order/reconnect;
- Telegram webhook secret/idempotency;
- provider policy snapshot;
- audit log;
- backup metadata;
- airport import.

## 22.5. E2E

Playwright own-app scenarios:

1. Bootstrap owner.
2. Invite second user.
3. Create household and verify isolation.
4. Search exact dates using Fake provider.
5. Search ±3 dates and see heatmap.
6. Enable nearby airports and compare net saving.
7. View direct, protected connection and split candidate.
8. Verify high-risk split hidden by default.
9. Create watch.
10. Simulate price history and material drop.
11. Verify one Telegram notification through fake sink.
12. Retry worker and verify no duplicate.
13. Click live refresh and verify UserActionGrant consumed once.
14. Verify background worker is denied for user-only fake provider.
15. Verify provider-isolated results not merged.
16. Click booking action and verify click-gated generation.
17. Pause/resume/archive watch.
18. Switch RU/EN and mobile viewport.
19. Admin disables provider and UI explains reason.
20. Privacy export/delete flow.

## 22.6. Quality gates

- domain/policy/itinerary/ranking ≥85% meaningful coverage;
- backend total ≥75%;
- frontend critical flow tests;
- lint/typecheck all green;
- no high/critical dependency vulnerabilities without documented exception;
- no secrets in repo/image/client bundle;
- migrations tested on empty and previous snapshot DB;
- Docker Compose smoke test.

---

# 23. DEMO MODE И FIXTURES

Продукт должен быть полностью демонстрируем без внешних ключей.

Создай deterministic fake scenarios:

- stable normal price;
- gradual drop;
- sudden anomaly;
- stale cached price;
- provider timeout then recovery;
- 429;
- direct vs one-stop;
- nearby airport gross saving but negative net saving;
- safe split-ticket;
- unsafe short self-transfer;
- provider-isolated live results;
- booking click gate;
- expired offer;
- missing baggage;
- currency conversion;
- Telegram alert dedupe.

Demo seed создаёт users/household/watches/history. UI явно показывает `DEMO DATA`, чтобы fake data нельзя было принять за настоящую.

---

# 24. CI/CD И DEPLOYMENT

## 24.1. GitHub Actions

Workflows:

- lint/typecheck;
- backend unit/integration;
- frontend unit;
- E2E compose;
- migration check;
- provider contract fixtures;
- secret scanning;
- dependency audit;
- container build/scan;
- SBOM;
- release image publish;
- manual provider smoke tests.

Используй caching, но не скрывай flaky tests retries. Исправляй flakiness.

## 24.2. Docker Compose

Обязательные services:

- web;
- api;
- worker;
- scheduler/beat, если отдельный;
- bot;
- postgres/postgis;
- redis;
- caddy;
- optional mail dev/fake Telegram sink;
- optional observability profile.

Требования:

- healthchecks;
- dependency conditions без бесконечного ожидания;
- named volumes;
- non-root;
- graceful shutdown;
- resource recommendations;
- no secrets baked into images;
- `.env.example`;
- dev/prod profiles;
- one-command seed/demo.

## 24.3. Backup/restore

- scheduled Postgres backup;
- encrypted archive option;
- retention;
- restore command;
- documented restore drill;
- verify backup age in admin;
- export object storage if used;
- migration compatibility notes.

## 24.4. Release/update

- semantic versioning;
- changelog;
- migration step;
- rollback notes;
- immutable image tags;
- upgrade command;
- backup before migration;
- release health check.

---

# 25. ДОКУМЕНТАЦИЯ — ОБЯЗАТЕЛЬНЫЕ ФАЙЛЫ

Создай и поддерживай:

- `README.md` — overview, screenshots, quick start, exact commands;
- `AGENTS.md`;
- `IMPLEMENTATION_STATUS.md`;
- `CHANGELOG.md`;
- `CONTRIBUTING.md`;
- `SECURITY.md`;
- `LICENSE` выбранной лицензии;
- `.env.example` с комментариями;
- `docs/ARCHITECTURE.md`;
- `docs/PROVIDER_MATRIX.md`;
- `docs/threat-model.md`;
- `docs/privacy/data-lifecycle.md`;
- `docs/provider-contracts/*.md`;
- `docs/runbooks/*.md`;
- `docs/adr/*.md`;
- OpenAPI docs;
- Telegram command/help docs;
- backup/restore docs;
- deployment docs.

README должен разделять:

- demo mode;
- Aviasales Data setup;
- optional provider access;
- ограничения live APIs;
- что cached цена не гарантирована;
- privacy/self-hosting;
- update/backup/restore.

---

# 26. ПОЭТАПНАЯ РЕАЛИЗАЦИЯ — ВСЕ ЭТАПЫ ОБЯЗАТЕЛЬНЫ

Работай фазами, но не останавливайся до конца. После каждой фазы запускай tests и обновляй status.

## Phase 0 — Discovery и ADR

- проверить versions;
- проверить provider docs;
- выбрать queue system/auth approach/chart library;
- записать ADR;
- создать implementation checklist;
- определить package boundaries.

Exit:

- ADR приняты;
- repo skeleton не содержит business implementation placeholders;
- local bootstrap documented.

## Phase 1 — Foundation

- monorepo/tooling;
- config/secrets;
- logging/tracing/metrics baseline;
- FastAPI/Next.js/worker/bot entrypoints;
- Postgres/Redis/Caddy Compose;
- CI baseline;
- health endpoints.

Exit:

- compose starts;
- tests/lint/typecheck run;
- no external key required.

## Phase 2 — Identity, household, audit

- owner bootstrap;
- invitation auth;
- household RBAC;
- preferences;
- sessions/CSRF;
- audit log;
- Telegram link model.

Exit:

- two-user isolation E2E;
- admin invite flow;
- security tests.

## Phase 3 — Provider Policy Engine

- policies/registry/guard;
- quotas;
- grants;
- merge scopes;
- admin policy view;
- invariants.

Exit:

- forbidden calls provably blocked;
- audit and metrics present.

## Phase 4 — Reference data и geo

- OurAirports importer;
- airport schema/PostGIS;
- autosuggest;
- nearby;
- metro groups;
- timezone;
- admin overrides/import health.

Exit:

- radius search correct;
- spatial index used;
- import idempotent.

## Phase 5 — Core search/domain

- SearchIntent;
- form schemas;
- NL parser/fallback;
- date matrix planner;
- search budgets;
- SSE progress;
- fake provider.

Exit:

- exact/flexible demo search end-to-end.

## Phase 6 — Aviasales Data

- typed client;
- auth/cache/rate limits;
- mapper;
- fixtures/contract tests;
- freshness labels;
- calendar/price routes;
- provider diagnostics.

Exit:

- works with key;
- graceful without key;
- cached semantics visible.

## Phase 7 — Canonical offers и ranking

- canonical model;
- normalization/provenance;
- dedupe;
- Pareto;
- presets;
- total cost;
- risk;
- result cards/compare.

Exit:

- deterministic ranking tests;
- unknown data handled honestly.

## Phase 8 — Itinerary Engine

- multi-city/open jaw;
- one-way pairing;
- split/self-transfer graph;
- buffers;
- risk gating;
- hidden-city experimental mode.

Exit:

- safe/unsafe fixture scenarios pass;
- risky variants not in default best.

## Phase 9 — Watches и history

- watch CRUD/versioning;
- scheduler/jobs;
- snapshots;
- adaptive intervals;
- policy-aware execution;
- history charts.

Exit:

- worker restart/retry safe;
- background forbidden provider not called.

## Phase 10 — Price intelligence и alerts

- percentile/MAD/trend;
- buy-now confidence;
- deal/anomaly detector;
- hot deals scanner;
- hysteresis/cooldown/dedupe;
- alert timeline.

Exit:

- simulated drop sends exactly one logical alert;
- insufficient data not overclaimed.

## Phase 11 — Telegram

- webhook/secret/idempotency;
- linking;
- commands;
- NL search;
- watch management;
- alerts/actions;
- click-gated live/booking flows.

Exit:

- E2E fake sink;
- retries no duplicate;
- unauthorized callback denied.

## Phase 12 — Optional live providers

- Duffel test/live adapter;
- Skyscanner Indicative/Live gated adapters;
- Aviasales Search isolated adapter disabled by default;
- policy/admin UX;
- live refresh flows.

Exit:

- contract fixtures pass;
- all unavailable states graceful;
- user action and isolation invariants pass.

## Phase 13 — Full UI polish

- dashboard;
- results/heatmap/nearby;
- watch detail;
- deals;
- admin;
- mobile/PWA;
- RU/EN;
- accessibility.

Exit:

- complete E2E matrix;
- no placeholder screens;
- mobile usable.

## Phase 14 — Security/operations

- threat model;
- redaction/SSRF/CSP;
- scans;
- backup/restore;
- runbooks;
- observability profile;
- performance/load tests.

Exit:

- restore drill documented/tested;
- no high/critical unresolved issue;
- dashboards/alerts useful.

## Phase 15 — Release readiness

- clean install test;
- upgrade/migration test;
- demo seed;
- docs/screenshots;
- changelog/version;
- final acceptance suite;
- remove all TODO/pass/fake production paths.

Exit:

- Definition of Done ниже выполнен полностью.

---

# 27. ACCEPTANCE SCENARIOS

Система считается готовой только если автоматизировано или воспроизводимо проходят сценарии.

## Scenario A — гибкие даты

Пользователь задаёт WAW → BCN, round trip, ±3 дня. Получает 7×7-compatible heatmap без 49 автоматических live вызовов, выбирает клетку и запускает разрешённый live refresh по клику.

## Scenario B — nearby airports

Пользователь ищет из Варшавы с радиусом 150 км. Система находит релевантные аэропорты, показывает расстояние/estimate и не называет airfare difference чистой экономией.

## Scenario C — split ticket

Есть дешёвые A→B и B→C отдельными билетами. Система проверяет chronology/buffer/baggage, показывает два PNR и risk. Небезопасная короткая пересадка скрыта default filter.

## Scenario D — cached vs live

Aviasales Data возвращает цену. Карточка показывает cached/freshness. User-only provider не вызывается до клика. После клика grant используется ровно один раз.

## Scenario E — Aviasales isolation

Даже при включённом тестовом Aviasales Search его результаты находятся в отдельном workspace и не влияют на merged best score.

## Scenario F — tracking

Watch выполняется scheduler-ом через permitted source, добавляет snapshot и не делает лишний запрос до TTL.

## Scenario G — alert

Цена падает на 12%. Создаётся один alert, Telegram получает одно сообщение. Retry не дублирует. Незначительное колебание не спамит.

## Scenario H — suspected anomaly

Цена резко ниже route history. Detector проверяет currency/passenger mismatch, маркирует suspicion, показывает confidence и предлагает live verification, не обещая ticketing.

## Scenario I — household privacy

Друг не видит searches/watches/alerts другого household ни через UI, ни через прямой API id.

## Scenario J — provider failure

429/timeout/schema drift одного optional provider не ломает search. Пользователь видит partial result; circuit breaker/metrics/admin diagnostics обновлены.

## Scenario K — no credentials

Чистая установка без API keys полностью работает в demo mode; settings точно объясняют, как подключить реальные источники.

## Scenario L — Telegram security

Поддельный webhook secret и чужой callback отклоняются. Link code одноразовый и истекает.

## Scenario M — booking click

Booking action, для которого требуется user click, не существует заранее в DB/message. Он создаётся только endpoint-ом после авторизованного клика.

## Scenario N — backup/restore

Созданные users, watches и history восстанавливаются в чистую instance по documented procedure.

## Scenario O — accessibility/i18n

Critical flows работают keyboard-only, на мобильном viewport и на RU/EN без raw keys.

---

# 28. NON-GOALS И ЗАПРЕТЫ

Не реализовывать как обязательную часть:

- автоматическую покупку билета;
- хранение банковских карт;
- оформление виз;
- обещание компенсации при missed self-transfer;
- universal prediction «лучший день недели для покупки»;
- scraping как fallback;
- bypass provider restrictions;
- публичный multi-tenant SaaS billing;
- Kubernetes-only deployment.

Запрещено оставлять:

- `TODO` в обязательных flows;
- `pass`/`NotImplementedError`;
- fake responses в production adapter path;
- secrets в repo;
- live calls в CI;
- money float;
- naive datetime;
- client-side provider tokens;
- silent exception swallowing;
- hidden cached/live distinction;
- unbounded search combinations;
- duplicate alerts;
- provider rules только в README без runtime enforcement.

---

# 29. ФИНАЛЬНЫЙ DEFINITION OF DONE

Не заканчивай работу, пока:

1. `docker compose up --build` поднимает stack.
2. `make seed-demo` создаёт полноценный сценарий.
3. Owner/invite/household isolation работают.
4. Airport import, autocomplete и nearby работают.
5. Search exact/flexible/multi-origin работает.
6. Aviasales Data adapter production-ready и graceful без key.
7. Provider Policy Engine защищает все calls.
8. Canonical normalization/dedupe работают.
9. Ranking/risk/total cost объяснимы.
10. Split/self-transfer engine работает и безопасно фильтрует.
11. Hidden-city research отделён и gated.
12. Watches/scheduler/history работают после restart/retry.
13. Price intelligence честно показывает confidence.
14. Deals/anomaly/alerts работают без спама.
15. Telegram linking/search/watch/alerts/actions работают.
16. Web UI завершён, responsive, PWA, RU/EN, accessible.
17. Optional live adapters корректно gated и не ломают instance.
18. Aviasales Search изолирован.
19. Booking click policy соблюдается.
20. Admin provider/job/audit/backup screens работают.
21. Security/privacy/threat model реализованы.
22. Backup/restore проверены.
23. Metrics/logs/traces/runbooks присутствуют.
24. CI quality/security/E2E проходят.
25. Clean install и upgrade test проходят.
26. Документация точна.
27. В обязательном production path нет placeholder/fake/TODO.

---

# 30. ФОРМАТ ТВОЕЙ РАБОТЫ И ФИНАЛЬНОГО ОТЧЁТА

В процессе:

- делай небольшие coherent commits;
- обновляй status;
- показывай фактические test results;
- не утверждай, что endpoint/provider работает live без credentials/smoke evidence;
- не скрывай внешние ограничения.

В финале выдай:

1. краткое описание архитектуры;
2. дерево ключевых файлов;
3. точные команды install/dev/test/prod/backup/restore;
4. таблицу providers: implemented/enabled/credentials/access/background/merge;
5. список завершённых acceptance scenarios;
6. test/lint/typecheck/security results;
7. известные ограничения, зависящие от внешнего доступа;
8. migration/upgrade notes;
9. список ADR;
10. подтверждение, что scraping/anti-bot bypass не используется.

Не называй работу завершённой на основании количества написанных файлов. Критерий — работающие flows и зелёная acceptance suite.
