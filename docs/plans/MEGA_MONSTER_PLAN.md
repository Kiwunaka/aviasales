# МЕГА МОНСТР ПЛАН.md

> Один большой промпт-план для coding agent. Работать в репозитории `Kiwunaka/aviasales` / `flight-hunter`. Не делать «демо ради демо». Цель — превратить текущий каркас в реально полезный self-hosted поисковик авиабилетов для себя и друзей: RU-first, RUB-first, cached + observed prices, внешние ссылки на покупку, редкие ручные/полуавтоматические browser observations, честная свежесть, история, сравнение, Telegram/PWA.

---

## Главная цель продукта

Собери self-hosted Flight Hunter, который умеет по запросу пользователя искать и сравнивать авиабилеты через доступные источники без B2B live API Aviasales Search. Приложение не продаёт билеты внутри себя. Оно:

- принимает человеческий запрос или форму: откуда, куда, даты, гибкость дат, пассажиры, багаж, пересадки, соседние аэропорты, допустимый риск;
- строит набор candidate-поисков: точные даты, ±N дней, nearby airports, open-jaw/multi-city где возможно, split-ticket/self-transfer candidates;
- берёт cached данные из Aviasales / Travelpayouts Data API;
- генерирует внешние click-out ссылки на RU-агрегаторы и сайты авиакомпаний;
- в personal/self-host режиме запускает browser observer для редкой проверки выдачи на конкретном сайте;
- парсит видимую страницу через Playwright + Scrapling/Crawl4AI/DOM-extractors;
- сохраняет observation с источником, временем, уверенностью, ссылкой и предупреждениями;
- сравнивает варианты по цене, длительности, пересадкам, багажу, свежести, риску и ground-transfer cost;
- показывает пользователю честные labels: `cached`, `api_cached`, `browser_observed`, `user_confirmed`, `stale`, `needs_external_confirmation`;
- отправляет Telegram-alert только когда есть действительно полезное изменение, с hysteresis/dedupe;
- никогда не делает вид, что cached цена является гарантированно доступной live-ценой.

Продукт должен быть ориентирован на RU-агрегаторы и RUB. Сначала считать источниками: Aviasales / Travelpayouts Data API, Aviasales click-out, Яндекс Путешествия click-out/browser observation, Туту click-out/browser observation, OneTwoTrip click-out/browser observation, официальные сайты авиакомпаний как secondary confirmation links: Аэрофлот, Победа, S7, Уральские авиалинии, Nordwind, Red Wings, Smartavia, Azimuth, Utair, Россия, Turkish Airlines, Air Serbia, Pegasus, Uzbekistan Airways, Emirates, Qatar, Etihad, Flydubai и другие по маршруту.

---

## Обязательные внешние факты, которые нельзя игнорировать

Ссылки проверены 2026-06-28. При реализации coding agent обязан при необходимости перепроверить документацию перед кодом.

- Aviasales Data API возвращает данные из кэша поисков пользователей Aviasales; данные хранятся 7 дней; цены нельзя показывать как live. Источник: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- `v3/prices_for_dates` возвращает cheapest tickets for specific dates, найденные пользователями за последние 48 часов, и отдаёт `link`, который добавляется к домену Aviasales для открытия результата. Источник: тот же Travelpayouts Data API doc.
- Data API имеет методы, которые надо использовать шире текущего адаптера: `v3/prices_for_dates`, `v3/get_latest_prices`, `v2/prices/month-matrix`, `v2/prices/week-matrix`, `v2/prices/nearest-places-matrix`, `v3/grouped_prices`, `v3/search_by_price_range`.
- Rate limits Travelpayouts Data API измеряются request/minute; опубликованы лимиты, например `/v3/prices_for_dates` 600 rpm, `/v3/get_latest_prices` 300 rpm, `/v2/prices/week-matrix` 60 rpm, `/v2/prices/nearest-places-matrix` 60 rpm. Внутренний лимитер проекта должен быть намного ниже и должен уважать `X-Rate-Limit-*`. Источник: https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits
- Aviasales Flight Search API доступен только проектам с подтверждёнными 50 000+ MAU; если MAU нет, официальная рекомендация — Data API. Источник: https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- Scrapling — adaptive web scraping framework; умеет parser, fetchers, spiders, adaptive selectors, sessions, browser/dynamic fetching. Его можно использовать как DOM parser и extraction layer. Источник: https://scrapling.readthedocs.io/en/latest/
- Scrapling `Selector` принимает HTML string/bytes и даёт CSS/XPath/text extraction API. Источник: https://scrapling.readthedocs.io/en/latest/parsing/main_classes.html
- Crawl4AI превращает web pages в LLM-ready Markdown, поддерживает async browser pool, caching, CSS/schema extraction, managed browser/persistent profiles, CLI/Docker. Источник: https://github.com/unclecode/crawl4ai и https://docs.crawl4ai.com/
- SearXNG поддерживает HTTP Search API на `/` и `/search`, GET/POST, `format=json/csv/rss`, но public instances часто отключают JSON/CSV/RSS, поэтому нужен self-host. Источник: https://docs.searxng.org/dev/search_api.html
- Playwright `launch_persistent_context(user_data_dir)` запускает persistent browser context с cookies/local storage; нельзя использовать основной Chrome profile, нужен отдельный automation profile. Источник: https://playwright.dev/python/docs/api/class-browsertype
- OurAirports публикует Public Domain CSV, обновляет dumps ночью, но точность не гарантирует. Источник: https://ourairports.com/data/

---

## Текущая база репозитория, от которой надо отталкиваться

В репозитории уже есть фундамент, его не выбрасывать:

- `README.md` описывает Flight Hunter как семейный self-hosted поиск/мониторинг, с честным cached/live distinction.
- `src/flight_hunter/application/search_service.py` сейчас orchestrates `SearchIntent`, `SearchPlanner`, `ProviderRegistry`, fake provider и optional providers.
- `src/flight_hunter/application/provider_registry.py` содержит policy definitions для fake, aviasales_data, aviasales_search, skyscanner, duffel.
- `src/flight_hunter/providers/aviasales_data/` уже имеет client, adapter, mapper, query planner, smoke helper.
- `src/flight_hunter/application/price_sources.py` уже содержит RUB-first каталог источников: Aviasales, Yandex Travel, Tutu, OneTwoTrip, Aeroflot, Pobeda, S7.
- `src/flight_hunter/application/live_observations.py` и `durable_live_observations.py` уже имеют grants, idempotency, fake browser source и fake worker.
- `src/flight_hunter/geo/` и airport import уже начали OurAirports direction.
- `src/flight_hunter/notifications/alerts.py` уже имеет hysteresis/dedupe logic.
- `src/flight_hunter/api/app.py` уже содержит FastAPI endpoints и простую web страницу.
- `pyproject.toml` сейчас Python 3.13+, FastAPI, SQLAlchemy, Alembic, `httpx2`, uv, pytest/ruff/mypy.

Не переписывать всё на другой стек. Развивать текущий Python/FastAPI модульный монолит. Добавлять frontend отдельно только если это реально нужно. Сначала можно расширить существующий FastAPI-served UI.

---

## Режим работы продукта

Flight Hunter должен иметь несколько source modes:

`api_cached`
: Официальный cached API. Например Travelpayouts / Aviasales Data API. Можно использовать для фонового мониторинга в пределах лимитов, для матриц, истории, дешёвых дат. UI всегда показывает source timestamp / found_at / observed_at / expires_at если есть.

`external_clickout`
: Ссылка на внешний поиск/покупку. Цена может быть неизвестна. Это не `FlightOffer`, если цены нет. Это `ExternalSearchLink`. Ссылка нужна всегда, даже когда нет цены.

`browser_observed`
: Цена считана из страницы браузером в self-host personal mode. Это observation, не гарантия покупки. Обязательно хранить `observed_at`, `source_id`, `final_url`, `confidence`, `parser_version`, `warnings`.

`manual_confirmed`
: Пользователь нажал “цена совпала/ниже/купил/неактуально”. Это отдельное событие, которое повышает confidence и может кормить историю.

`deal_feed`
: Сделки/акции/форумы/рассылки/RSS/SearXNG/Crawl4AI. Это candidate generator, не источник истины цены.

`carrier_confirmation`
: Ссылка или observation на сайте авиакомпании. Используется как дополнительная проверка условий, багажа, тарифа.

---

## Необходимая доменная модель

Текущий `FlightOffer` слишком узкий: требует цену. Надо добавить новые сущности, не ломая старые тесты.

Добавить в `src/flight_hunter/domain/offers.py` или новые файлы `domain/search_results.py`, `domain/observations.py`:

```python
class ResultKind(StrEnum):
    PRICED_OFFER = "priced_offer"
    EXTERNAL_SEARCH_LINK = "external_search_link"
    BROWSER_OBSERVATION = "browser_observation"
    DEAL_CANDIDATE = "deal_candidate"
    CARRIER_CONFIRMATION_LINK = "carrier_confirmation_link"

class Freshness(StrEnum):
    LIVE_OBSERVED = "live_observed"
    USER_CONFIRMED = "user_confirmed"
    BROWSER_OBSERVED = "browser_observed"
    API_CACHED = "api_cached"
    CACHED = "cached"
    STALE = "stale"
    UNKNOWN_EXTERNAL = "unknown_external"

@dataclass(frozen=True, slots=True)
class ExternalSearchLink:
    source_id: str
    source_name: str
    url: str
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    passengers: int
    adults: int
    children: int
    infants: int
    currency: str
    source_type: Literal["aggregator", "carrier", "search", "deal"]
    purchase_flow: Literal["external_clickout", "external_search", "manual_check"]
    price_known: bool = False
    requires_external_confirmation: bool = True
    notes_ru: str | None = None

@dataclass(frozen=True, slots=True)
class BrowserObservedOffer:
    observation_id: UUID
    source_id: str
    source_name: str
    provider_offer_id: str
    origin: str
    destination: str
    departure_date: str | None
    return_date: str | None
    total_price: Money | None
    passengers: int
    observed_at: datetime
    final_url: str
    display_url: str
    freshness: Freshness
    confidence: Literal["none", "low", "medium", "high"]
    parser_version: str
    parser_warnings: tuple[str, ...]
    airline_name: str | None = None
    airline_iata: str | None = None
    flight_number: str | None = None
    departure_time_local: str | None = None
    arrival_time_local: str | None = None
    duration_minutes: int | None = None
    stops: int | None = None
    baggage_summary: str | None = None
    seller_name: str | None = None
    requires_external_confirmation: bool = True

@dataclass(frozen=True, slots=True)
class SearchBundle:
    search_id: str
    priced_offers: tuple[FlightOffer, ...]
    browser_observed_offers: tuple[BrowserObservedOffer, ...]
    external_links: tuple[ExternalSearchLink, ...]
    deal_candidates: tuple[DealCandidate, ...]
    denied_sources: Mapping[str, ProviderDenial]
    warnings: tuple[str, ...]
```

Цель: API должен возвращать не только `offers`, но и `external_links`, `observations`, `warnings`, `freshness_summary`.

---

## Главный поисковый конвейер

Собери такой pipeline:

```text
User/SearchIntent
  -> IntentValidator
  -> AirportResolver / NearbyResolver
  -> DateWindowPlanner
  -> CandidatePlanner
  -> SourceTaskPlanner
  -> API Cached Providers
  -> External Link Builders
  -> Browser Observation Grants / Jobs
  -> DOM Fetch / Browser Session / Scrapling Parser / Crawl4AI Markdown Parser
  -> Normalization
  -> Dedupe / Fingerprint
  -> Risk & Total Cost
  -> Ranking / Pareto Frontier
  -> Persistence snapshots
  -> UI / Telegram
```

Важно: browser observation не обязан запускаться для всех ссылок сразу. UI должен показать кнопки: “Открыть”, “Считать из браузера”, “Подтвердить цену”, “Неактуально”, “Следить”.

Для self-host режима можно добавить настройку `PERSONAL_OBSERVER_AUTO_RUN=true`, но default лучше `false`/ручной запуск из UI, потому что это редкие запросы и так будет стабильнее.

---

## SearchIntent нужно расширить

Текущий `SearchIntent` принимает только IATA origin/destination, date, return_date, passengers, currency. Нужно добавить:

```python
@dataclass(frozen=True, slots=True)
class SearchIntent:
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    passengers: int
    currency: str
    adults: int | None = None
    children: int = 0
    infants: int = 0
    trip_type: TripType | str | None = None
    cabin: CabinClass = CabinClass.ECONOMY
    baggage: BaggagePreference = BaggagePreference.UNKNOWN
    max_stops: int | None = None
    direct_only: bool = False
    flexible_days: int = 0
    min_stay_days: int | None = None
    max_stay_days: int | None = None
    nearby_origin_radius_km: int = 0
    nearby_destination_radius_km: int = 0
    allow_self_transfer: bool = False
    allow_split_ticket: bool = False
    allow_airport_change: bool = False
    allow_overnight: bool = False
    max_total_duration_minutes: int | None = None
    max_price_minor_units: int | None = None
    preferred_sources: tuple[str, ...] = ()
    excluded_sources: tuple[str, ...] = ()
    ru_market_only: bool = True
    request_locale: str = "ru-RU"
```

Validator должен:

- проверять IATA/city code;
- не пропускать детей/младенцев в источники, которые не умеют passenger mix;
- явно маркировать degraded search;
- не выдумывать коды аэропортов;
- сохранять normalized intent fingerprint, включающий все значимые поля.

---

## Источники и их роли

### Aviasales Data API

Расширить `src/flight_hunter/providers/aviasales_data/`:

```text
client.py
adapter.py
mapper.py
query_planner.py
endpoints.py
models.py
rate_limit.py
cache.py
link_builder.py
fixtures/
```

Реализовать endpoints:

- `prices_for_dates`
- `get_latest_prices`
- `month_matrix`
- `week_matrix`
- `nearest_places_matrix`
- `grouped_prices`
- `search_by_price_range`, если документация подтверждает текущую доступность

Для каждого endpoint:

- typed query dataclass;
- typed response dataclass;
- safe parser с unknown fields bag;
- mapping warnings;
- `found_at`, `expires_at`, `actual`, `link`, `gate`, `number_of_changes`, `duration`, `distance` сохранять;
- не умножать цену на passengers без проверки смысла source price; если API возвращает price per ticket, явно хранить `price_basis`.

Внутренний лимитер:

```python
@dataclass(frozen=True, slots=True)
class RateLimitState:
    provider_id: str
    endpoint: str
    limit_per_minute: int
    remaining: int | None
    reset_after_seconds: int | None
    observed_at: datetime
```

При 429:

- не падать всем поиском;
- вернуть denied/source warning;
- поставить cooldown;
- сохранить provider health.

### RU click-out sources

Добавить `src/flight_hunter/providers/ru_clickout/`:

```text
catalog.py
models.py
link_builder.py
adapter.py
source_specs.py
```

`source_specs.py` должен описывать:

```python
@dataclass(frozen=True, slots=True)
class RuAggregatorSpec:
    source_id: str
    display_name: str
    base_url: str
    allowed_hosts: tuple[str, ...]
    supports_one_way: bool
    supports_round_trip: bool
    supports_multi_city: bool
    supports_passenger_mix: bool
    supports_children: bool
    supports_infants: bool
    supports_baggage_query: bool
    supports_currency_param: bool
    default_currency: str
    link_strategy: Literal["known_template", "search_page", "query_search", "manual"]
    browser_observation_allowed: bool
    parser_id: str | None
```

Начальные sources:

```text
aviasales_clickout
travelpayouts_aviasales_deeplink
yandex_travel
tutu
onetwotrip
aeroflot
pobeda
s7
```

Если точный URL-шаблон нестабилен или неизвестен — не выдумывать. Делать `search_page` link: источник + понятная query string / prefilled form where possible. Для таких источников UI показывает “Открыть поиск на сайте”, а не “готовый билет”.

### Browser observer sources

Добавить `src/flight_hunter/providers/personal_observer/`:

```text
__init__.py
config.py
source_specs.py
browser_runner.py
dom_snapshot.py
extractors/
  base.py
  common.py
  aviasales.py
  yandex_travel.py
  tutu.py
  onetwotrip.py
  carrier_generic.py
scrapling_parser.py
crawl4ai_parser.py
normalizer.py
adapter.py
errors.py
```

`browser_runner.py`:

- Playwright persistent context;
- отдельный profile dir: `.local/browser-profiles/{source_id}`;
- visible mode по умолчанию для local self-host;
- headless mode allowed only by env;
- navigation timeout;
- wait strategy: `domcontentloaded`, optional network idle, optional selector wait;
- manual checkpoint: “дойди до выдачи и нажми кнопку считать”;
- save sanitized DOM snapshot only if `PERSONAL_OBSERVER_SAVE_DOM_FIXTURES=true`;
- screenshot only if debug flag;
- never log cookies/local storage/tokens.

`dom_snapshot.py`:

```python
@dataclass(frozen=True, slots=True)
class DomSnapshot:
    source_id: str
    requested_url: str
    final_url: str
    title: str | None
    html: str
    text: str
    captured_at: datetime
    visible_text_hash: str
    html_hash: str
    screenshot_path: str | None
```

`extractors/base.py`:

```python
class BrowserOfferExtractor(Protocol):
    parser_id: str
    parser_version: str
    supported_source_ids: tuple[str, ...]

    def extract(self, snapshot: DomSnapshot, intent: SearchIntent) -> BrowserExtractionResult: ...
```

`BrowserExtractionResult`:

```python
@dataclass(frozen=True, slots=True)
class BrowserExtractionResult:
    offers: tuple[BrowserObservedOffer, ...]
    warnings: tuple[str, ...]
    confidence: Literal["none", "low", "medium", "high"]
    raw_price_candidates: tuple[PriceCandidate, ...]
```

Common parser rules:

- first try source-specific CSS/XPath selectors;
- then Scrapling `Selector(html)` extraction;
- then regex price fallback on visible text;
- then optional Crawl4AI markdown extraction for deal pages / not structured results;
- then optional local LLM extraction only from sanitized text, not from cookies/raw secrets;
- if result has price but no route/date match, confidence max `low`;
- if price + route/date + source card boundaries found, confidence `medium`/`high`;
- always store parser warnings.

Price extraction must avoid false positives:

```python
PRICE_RE = r"(?<!\d)(\d[\d\s\u00a0]{2,8})\s*(₽|руб\.?|RUB)(?!\w)"
```

Filter suspicious values:

- below 500 RUB: ignore for airfare;
- above 2_000_000 RUB: ignore unless business/first/family big passenger mix;
- duplicated values dedupe;
- baggage/seat/insurance values must not become total fare unless card context says total.

### Crawl4AI role

Crawl4AI использовать для:

- deal pages;
- форумов;
- markdown extraction;
- long pages with many links;
- SearXNG result follow-up;
- extracting structured JSON from articles/feeds.

Не делать Crawl4AI главным парсером RU aggregator result pages. Для aggregator result pages сначала Playwright DOM snapshot + Scrapling/selector extractors.

### SearXNG role

Self-host SearXNG as discovery engine:

```text
searxng -> DealDiscoveryService -> Crawl4AI -> DealCandidate -> Human/user verification -> SearchIntent/Watch suggestion
```

Queries:

- `site:forum.awd.ru авиабилеты {origin} {destination} {month}`
- `site:travelradar.ru авиабилеты {destination} распродажа`
- `site:tripster.ru авиабилеты акция {destination}`
- `авиабилеты {origin} {destination} дешево {month} руб`
- `распродажа авиабилетов {carrier} {destination}`

SearXNG results are not price truth. They create candidates and hints.

---

## Source policy без самообмана

Не удалять policy engine. Переделать policy так, чтобы она разрешала personal scraping mode, но не смешивала всё в одну кашу.

Добавить:

```python
class DataKind(StrEnum):
    CACHED = "cached"
    INDICATIVE = "indicative"
    LIVE = "live"
    BOOKABLE = "bookable"
    FEED = "feed"
    EXTERNAL_LINK = "external_link"
    BROWSER_OBSERVED = "browser_observed"
    USER_CONFIRMED = "user_confirmed"

class ExecutionContext(StrEnum):
    WEB_USER_ACTION = "web_user_action"
    TELEGRAM_CALLBACK = "telegram_callback"
    SCHEDULER = "scheduler"
    WORKER = "worker"
    PERSONAL_LOCAL_BROWSER = "personal_local_browser"
    PERSONAL_MANUAL_CONFIRMATION = "personal_manual_confirmation"

class ProviderOperation(StrEnum):
    SEARCH = "search"
    BOOKING_ACTION = "booking_action"
    LIVE_REFRESH = "live_refresh"
    EXTERNAL_LINK_BUILD = "external_link_build"
    BROWSER_OBSERVE = "browser_observe"
    DEAL_DISCOVERY = "deal_discovery"
```

Для personal observer:

```python
ProviderPolicy(
    provider_id="tutu_browser",
    data_kind=DataKind.BROWSER_OBSERVED,
    background_requests_allowed=False,
    user_action_required=True,
    merge_with_other_sources_allowed=True,  # но с freshness/risk penalty
    persist_raw_results_allowed=False,
    persist_normalized_results_allowed=True,
    booking_link_requires_click=True,
    preload_booking_links_allowed=False,
    server_side_only=True,
    real_user_ip_required=False,
    max_requests_per_minute=1,
    max_requests_per_hour_per_user_ip=5,
    cache_ttl_seconds=0,
    result_ttl_seconds=300,
    max_concurrent_requests=1,
)
```

Смысл: self-host scraping разрешён в продукте как user-action personal observer, но результат живёт коротко и не считается гарантированной покупкой.

---

## Browser observation UX

В UI каждая карточка должна иметь:

```text
[Открыть на Aviasales]
[Открыть на Яндекс Путешествия]
[Открыть на Туту]
[Открыть на OneTwoTrip]
[Считать цену из открытого браузера]
[Я подтвердил цену]
[Цена неактуальна]
[Следить]
```

Когда пользователь нажимает “Считать цену”:

1. API создаёт `UserActionGrant`.
2. API создаёт `BrowserObservationJob`.
3. Worker запускает visible browser или подключается к existing browser profile.
4. UI показывает статус: `opening_browser`, `waiting_for_user`, `capturing_dom`, `parsing`, `succeeded`, `needs_human`, `failed`.
5. Если сайт требует ручного действия, job остаётся `waiting_for_user` и показывает instruction.
6. После считывания DOM результат возвращается в UI.
7. UI не скрывает warnings.

API endpoints:

```text
POST /api/v1/external-links/build
POST /api/v1/personal-observations/grants
POST /api/v1/personal-observations
GET  /api/v1/personal-observations/{id}
POST /api/v1/personal-observations/{id}/confirm
POST /api/v1/personal-observations/{id}/mark-stale
GET  /api/v1/browser-sources
POST /api/v1/browser-sources/{source_id}/test-parser
```

CLI:

```text
uv run flight-hunter-observe --source tutu --origin MOW --destination IST --depart 2026-09-10 --return 2026-09-20 --passengers 1
uv run flight-hunter-observe --url "https://..." --source yandex_travel --interactive
uv run flight-hunter-parse-fixture fixtures/browser/tutu/mow-ist.html --source tutu
uv run flight-hunter-source-smoke --source aviasales_data
uv run flight-hunter-source-smoke --source searxng
```

---

## Persistence / DB schema

Добавить Alembic migrations. Не хранить raw HTML по умолчанию. Для debug fixtures — только локальные файлы под `.local/` или `fixtures/sanitized/` без cookies/tokens.

Таблицы:

```text
external_search_links
  id uuid pk
  household_id uuid nullable
  user_id uuid nullable
  source_id text
  source_name text
  origin text
  destination text
  departure_date date
  return_date date null
  passenger_fingerprint text
  currency text
  url text
  url_hash text
  created_at timestamptz
  expires_at timestamptz null
  notes_ru text null

browser_observation_jobs
  id uuid pk
  household_id uuid
  user_id uuid
  source_id text
  search_intent_hash text
  requested_url text
  idempotency_key text
  status text
  grant_id uuid
  created_at timestamptz
  started_at timestamptz null
  waiting_since timestamptz null
  completed_at timestamptz null
  expires_at timestamptz
  error_code text null
  error_message text null

browser_observed_offers
  id uuid pk
  observation_job_id uuid fk
  source_id text
  provider_offer_id text
  origin text null
  destination text null
  departure_date date null
  return_date date null
  amount_minor_units bigint null
  currency text null
  passengers int
  observed_at timestamptz
  final_url text
  final_url_hash text
  parser_id text
  parser_version text
  confidence text
  warnings_json jsonb/text
  airline_name text null
  flight_number text null
  departure_time_local text null
  arrival_time_local text null
  duration_minutes int null
  stops int null
  baggage_summary text null
  seller_name text null

manual_price_confirmations
  id uuid pk
  observed_offer_id uuid null
  external_search_link_id uuid null
  user_id uuid
  status text -- confirmed/sold_out/price_changed/bought/wrong_route
  amount_minor_units bigint null
  currency text null
  note text null
  confirmed_at timestamptz

source_health_events
  id uuid pk
  source_id text
  event_type text
  status text
  message text
  observed_at timestamptz
  cooldown_until timestamptz null

deal_candidates
  id uuid pk
  source_id text
  discovered_url text
  title text
  summary text
  extracted_origin text null
  extracted_destination text null
  extracted_departure_window text null
  extracted_price_minor_units bigint null
  currency text null
  confidence text
  discovered_at timestamptz
  raw_ref text null
```

SQLite-compatible first, Postgres JSONB later if needed. Migrations must pass SQLite tests and not require local Postgres for unit tests.

---

## Ranking и сравнение

Ranker должен учитывать:

```text
effective_price = fare + known_baggage + estimated_ground_transfer + self_transfer_contingency + overnight_estimate
score = price_weight + duration_weight + stops_weight + freshness_weight + risk_weight + confidence_weight
```

Freshness penalty:

```text
browser_observed <= 5 min: very low penalty
user_confirmed <= 5 min: lowest penalty
api_cached found_at <= 48h: medium penalty
api_cached > 48h or expires_at passed: high penalty/stale
external_link no price: not ranked as price, shown as action
```

Risk penalty:

- split-ticket: +risk;
- self-transfer: +risk;
- airport change: +risk;
- overnight: +risk/hotel estimate;
- baggage unknown: +risk if passenger requested baggage;
- route/date mismatch from parser: confidence low.

Dedupe fingerprint:

```text
source_id + normalized route + local departure date/time + airline/flight number + seller + baggage + passenger mix + price basis
```

Do not collapse offers from different sellers if conditions differ.

---

## Itinerary / split / self-transfer

Добавить `src/flight_hunter/itinerary_engine/`:

```text
models.py
candidate_graph.py
connection_rules.py
beam_search.py
risk.py
composer.py
```

Minimum viable logic:

- Direct / one-ticket result from provider is safest.
- Split-ticket = two independent offers; display as experimental and rank only if saving is meaningful.
- Self-transfer needs configurable buffers:
  - domestic same airport no baggage: minimum 2h;
  - international same airport no baggage: minimum 3h;
  - checked baggage: +1h;
  - airport change: +2h plus ground transfer;
  - overnight if arrival/departure crosses night.
- If visa/entry unknown: warning, not hard claim.
- Hidden-city research stays disabled unless explicit feature flag and warning acknowledgement.

No magic. Every risky candidate must show why it is risky.

---

## Airports / geography

OurAirports importer must become production-useful:

- import `airports.csv`, `countries.csv`, `regions.csv`;
- filter closed airports, heliports, small/private fields by default;
- keep only commercial relevant airports unless admin includes;
- store coordinates, municipality, country, region, IATA, ICAO, type, scheduled_service if present;
- support metro groups and city codes;
- allow admin override for city/airport aliasing;
- add ground transfer estimate with confidence.

Nearby search:

```text
origin candidates = requested airport/city + airports within radius + configured nearby city group
candidate cost = distance_km, estimated_minutes, estimated_ground_cost, relevance penalty
```

For Moscow, Istanbul, Berlin, Warsaw, Paris, London and similar multi-airport cities, hardcode useful metro groups only as curated override, not fake API data.

---

## Telegram и watches

Watches должны работать не как live spam, а как scheduled candidate scan:

- cached Aviasales Data API scan allowed within internal rpm/cooldown;
- browser observer not run in background by default;
- Telegram alert can include “есть candidate, нажми проверить в браузере”;
- if user taps Telegram callback “Проверить”, create user action grant and browser observation job;
- alert dedupe by route/date/passenger/source/price bucket;
- hysteresis: don’t alert small wiggles;
- quiet hours;
- per-household isolation.

Telegram messages:

```text
Нашёл вариант MOW → IST 12–20 сентября:
• Aviasales Data: 18 420 ₽, cached, найдено 6 ч назад
• Туту/Яндекс/OneTwoTrip: ссылки для проверки
• Почему интересно: на 14% ниже медианы твоих наблюдений
[Проверить в браузере] [Открыть Aviasales] [Следить] [Скрыть]
```

---

## UI / Web

Существующий FastAPI HTML можно временно расширить. Финальный Next.js/PWA не обязателен прямо сейчас.

Нужные экраны:

- Главная форма поиска.
- Advanced drawer: flexible days, nearby radius, baggage, max stops, split/self-transfer toggles.
- Results split by source:
  - “Цены из кэша”;
  - “Свежие наблюдения из браузера”;
  - “Ссылки для проверки”;
  - “Сделки/форумы”.
- Карточка результата:
  - price;
  - source;
  - freshness badge;
  - observed/found time;
  - route details;
  - baggage unknown/known;
  - risks;
  - buttons.
- Browser observation status modal:
  - source;
  - opened URL;
  - status;
  - instruction;
  - result preview;
  - confirm/stale buttons.
- History chart per watch.
- Provider health page.
- Parser diagnostics page only in dev/admin mode.

No UI claim “купить здесь”. Use “Открыть на сайте” / “Проверить цену” / “Перейти к покупке на внешнем сайте”.

---

## Config / environment

Add to `.env.example`:

```env
# Personal browser observer
PERSONAL_OBSERVER_ENABLED=false
PERSONAL_OBSERVER_HEADLESS=false
PERSONAL_OBSERVER_PROFILE_ROOT=.local/browser-profiles
PERSONAL_OBSERVER_SAVE_DOM_FIXTURES=false
PERSONAL_OBSERVER_SAVE_SCREENSHOTS=false
PERSONAL_OBSERVER_MAX_CONCURRENT=1
PERSONAL_OBSERVER_MIN_GAP_SECONDS=60
PERSONAL_OBSERVER_RESULT_TTL_SECONDS=300
PERSONAL_OBSERVER_ALLOWED_HOSTS=aviasales.ru,www.aviasales.ru,travel.yandex.ru,www.tutu.ru,avia.tutu.ru,www.onetwotrip.com
PERSONAL_OBSERVER_REQUIRE_USER_ACTION=true
PERSONAL_OBSERVER_AUTO_RUN=false

# Scrapling
SCRAPLING_ENABLED=true
SCRAPLING_ADAPTIVE_STORAGE=.local/scrapling-adaptive
SCRAPLING_USE_FETCHERS=false
SCRAPLING_USE_SPIDERS=false

# Crawl4AI
CRAWL4AI_ENABLED=false
CRAWL4AI_MODE=library
CRAWL4AI_CACHE_DIR=.local/crawl4ai-cache

# SearXNG
SEARXNG_ENABLED=false
SEARXNG_BASE_URL=http://127.0.0.1:8080
SEARXNG_FORMAT=json
SEARXNG_TIMEOUT_SECONDS=15

# Source behaviour
RU_AGGREGATORS_ENABLED=aviasales_clickout,yandex_travel,tutu,onetwotrip
CARRIER_LINKS_ENABLED=aeroflot,pobeda,s7
SOURCE_INTERNAL_RPM=10
```

Add dependency groups:

```toml
[dependency-groups]
scraping = [
  "playwright>=1.50,<2.0",
  "scrapling>=0.2,<1.0",
  "beautifulsoup4>=4.12,<5.0",
]
crawler = [
  "crawl4ai>=0.7,<1.0",
]
```

Pin exact versions after checking current releases. If `scrapling[fetchers]` pulls browser/fingerprint deps, keep it optional. Core parser can be installed separately.

---

## Docker Compose self-host

Add optional compose profile:

```yaml
services:
  api:
    profiles: ["default"]
  worker:
    profiles: ["worker"]
  searxng:
    profiles: ["search"]
  browser:
    profiles: ["browser"]
```

But for local Windows/Mac beginner mode, CLI visible browser is more useful than browser container. Do not block local usage on Docker.

SearXNG self-host:

- enable JSON output in settings;
- restrict access to LAN/local auth;
- do not expose publicly without auth;
- rate limit.

---

## Testing strategy

No CI scraping of live RU sites. CI uses fixtures.

Required tests:

```text
tests/unit/domain/test_external_search_link.py
tests/unit/domain/test_browser_observed_offer.py
tests/unit/providers/ru_clickout/test_link_builder.py
tests/unit/providers/personal_observer/test_price_extraction.py
tests/unit/providers/personal_observer/test_scrapling_parser.py
tests/unit/providers/personal_observer/test_source_extractors.py
tests/unit/application/test_search_bundle_service.py
tests/unit/api/test_external_links_api.py
tests/unit/api/test_personal_observation_api.py
tests/unit/persistence/test_browser_observation_migrations.py
tests/unit/persistence/test_observation_repository.py
tests/unit/application/test_browser_observation_service.py
tests/unit/application/test_deal_discovery_service.py
tests/unit/providers/aviasales_data/test_latest_prices.py
tests/unit/providers/aviasales_data/test_week_matrix.py
tests/unit/providers/aviasales_data/test_rate_limit_headers.py
```

Fixtures:

```text
fixtures/browser/aviasales/search_result_sanitized.html
fixtures/browser/yandex_travel/search_result_sanitized.html
fixtures/browser/tutu/search_result_sanitized.html
fixtures/browser/onetwotrip/search_result_sanitized.html
fixtures/browser/carrier_generic/search_result_sanitized.html
fixtures/aviasales_data/prices_for_dates_success.json
fixtures/aviasales_data/get_latest_prices_success.json
fixtures/aviasales_data/week_matrix_success.json
fixtures/searxng/search_results.json
fixtures/crawl4ai/deal_page_markdown.md
```

Fixture rules:

- no cookies;
- no personal data;
- no tokens;
- no full copyrighted page dumps committed if avoidable; prefer minimal sanitized snippets with card structure;
- if committing larger HTML fixtures, keep them generated/synthetic or local-only.

Parser acceptance:

- extracts at least one price from each fixture;
- does not extract baggage upsell as total fare;
- detects no price and returns `confidence=none`;
- detects wrong route/date and returns low confidence warning;
- source-specific parser failure triggers fallback parser;
- parser version is visible in output.

---

## API response shape

Update `/api/v1/searches` response:

```json
{
  "search_id": "sha256:...",
  "priced_offers": [],
  "browser_observed_offers": [],
  "external_links": [],
  "deal_candidates": [],
  "denied_providers": {},
  "warnings": [],
  "freshness_summary": {
    "best_price_source": "aviasales_data",
    "freshest_observation_at": null,
    "needs_external_confirmation": true
  }
}
```

Keep backwards compatibility by allowing old `offers` field until UI/tests are migrated.

---

## Link builders

Implement link builders with conservative contracts:

```python
class ExternalLinkBuilder(Protocol):
    source_id: str
    def can_build(self, intent: SearchIntent) -> bool: ...
    def build(self, intent: SearchIntent) -> ExternalSearchLink: ...
```

For Aviasales Data `link` field:

- add it to Aviasales base URL;
- if partner marker configured, wrap with partner link if docs support;
- keep raw path only as `provider_link_path`, not as final purchase guarantee.

For sources without stable deep link:

- generate site search URL or homepage URL with notes;
- UI says “Открыть и заполнить/проверить”.

Do not fake a precise route/date deeplink if source format is unknown.

---

## Deal discovery

Add:

```text
src/flight_hunter/deals/
  models.py
  searxng_client.py
  crawl4ai_client.py
  query_builder.py
  extractor.py
  service.py
```

`DealCandidate`:

```python
@dataclass(frozen=True, slots=True)
class DealCandidate:
    source_id: str
    url: str
    title: str
    summary_ru: str
    extracted_price: Money | None
    extracted_origin: str | None
    extracted_destination: str | None
    extracted_date_window: str | None
    confidence: Literal["low", "medium", "high"]
    discovered_at: datetime
    requires_manual_verification: bool = True
```

Deal discovery runs manually or low-frequency, never blocks normal search. It enriches UI with “возможно есть акция”.

---

## Worker / queue

Current app can run in-process for demo, but real browser jobs must not block API request.

Add minimal worker abstraction:

```python
class JobQueue(Protocol):
    async def enqueue_browser_observation(...): ...
    async def enqueue_watch_scan(...): ...
```

Implement first:

- `InProcessJobQueue` for local dev;
- `SQLiteJobQueue` or DB-backed polling worker;
- later Redis/Dramatiq/Celery.

Worker command:

```text
uv run flight-hunter-worker
```

Worker responsibilities:

- process browser observations;
- process watch scans;
- cleanup expired observations;
- record source health;
- never print secrets.

---

## Security / privacy / local files

Even for pet project:

- never commit `.env`, browser profiles, cookies, screenshots with personal data;
- `.local/` in `.gitignore`;
- token values must not appear in logs;
- `AdminProviderHealth` shows boolean secret presence only;
- browser profile path under project-local `.local/browser-profiles/{source}`;
- raw HTML retention default off;
- if saving raw HTML for parser work, provide `sanitize-fixture` command.

Add commands:

```text
uv run flight-hunter-sanitize-html --input .local/raw.html --output fixtures/browser/tutu/minimal.html
uv run flight-hunter-redact-url --url "..."
```

---

## Error model

Every source failure must be typed:

```python
class SourceErrorCode(StrEnum):
    SOURCE_DISABLED = "source_disabled"
    CREDENTIALS_MISSING = "credentials_missing"
    RATE_LIMITED = "rate_limited"
    HTTP_ERROR = "http_error"
    PARSER_NO_PRICE = "parser_no_price"
    PARSER_ROUTE_MISMATCH = "parser_route_mismatch"
    BROWSER_TIMEOUT = "browser_timeout"
    WAITING_FOR_USER = "waiting_for_user"
    SOURCE_LAYOUT_CHANGED = "source_layout_changed"
    SOURCE_BLOCKED = "source_blocked"
    UNKNOWN = "unknown"
```

Do not throw raw exceptions to UI. Return source-specific warnings.

---

## Observability

Add structured logging:

```text
event=search_started search_id=... household_id=...
event=provider_call provider=aviasales_data endpoint=prices_for_dates duration_ms=...
event=browser_observation_started source=tutu job_id=...
event=parser_result source=tutu offers=3 confidence=medium warnings=...
event=alert_sent watch_id=... reason=price_drop
```

Metrics if Prometheus available:

```text
flight_hunter_provider_requests_total
flight_hunter_provider_errors_total
flight_hunter_browser_observation_jobs_total
flight_hunter_parser_offers_extracted_total
flight_hunter_search_duration_seconds
flight_hunter_alerts_sent_total
```

---

## Coding agent operating rules

Ты coding agent. Работай как senior engineer, а не как генератор заглушек.

Перед кодом:

- прочитай `README.md`, `docs/ARCHITECTURE.md`, `docs/PROVIDER_MATRIX.md`, `IMPLEMENTATION_STATUS.md`, `AGENTS.md`, `MEGA_PROMPT.md` если есть;
- проверь текущие версии библиотек и docs;
- не стирай существующую архитектуру без причины;
- сначала добавь тесты на новое поведение;
- потом код;
- потом миграции;
- потом docs;
- потом запусти tests/lint/typecheck.

Не использовать слова “готово”, если не прошли exit criteria.

Не оставлять `TODO`, `pass`, `NotImplementedError` в production path.

Не добавлять fake worker в real path. Fake допустим только в tests/demo provider.

Не писать “live”, если source cached/observed/unknown.

Не хранить raw secrets.

Не зависеть от реального live сайта в unit tests.

---

## Команды проверки

После изменения обязательно:

```powershell
uv sync --group dev --group scraping
uv run pytest tests/unit --quiet
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run alembic upgrade head
uv run travelpayouts-smoke
uv run flight-hunter-source-smoke --source aviasales_data
```

Если установлен browser stack:

```powershell
uv run playwright install chromium
uv run flight-hunter-observe --source tutu --origin MOW --destination IST --depart 2026-09-10 --return 2026-09-20 --passengers 1 --interactive
```

Если SearXNG включён:

```powershell
uv run flight-hunter-source-smoke --source searxng
```

---

## Definition of Done

Считать работу достаточной, когда выполняется всё ниже:

- `/api/v1/searches` возвращает priced cached offers + external links.
- Aviasales Data adapter умеет не только `prices_for_dates`, но и хотя бы один matrix/latest endpoint.
- Для RU-агрегаторов есть `ExternalSearchLink` генерация.
- Есть personal browser observation job с visible Playwright browser.
- Есть Scrapling-based DOM parser, который работает на sanitized fixtures.
- Есть хотя бы один source-specific extractor: Tutu или Yandex Travel или Aviasales page.
- Browser observation сохраняет normalized result в БД.
- UI показывает source/freshness/confidence/warnings.
- Telegram/watch не запускает browser observation без user action, а предлагает кнопку проверки.
- Tests/lint/mypy проходят.
- Docs объясняют режимы: cached, external link, browser observed, manual confirmed.
- README больше не говорит, что scraping отсутствует вообще; он говорит, что scraping есть только в self-host personal observer mode и выключен по умолчанию.

---

## Как переписать README

Заменить старую формулировку про scraping на такую:

```text
По умолчанию Flight Hunter не делает скрытый массовый scraping и не обещает live-цены там, где источник даёт cache.

Для self-host/personal режима есть Personal Browser Observer:
- запускается только владельцем/пользователем;
- открывает видимый или локальный browser profile;
- считывает результат внешнего сайта как browser observation;
- сохраняет только нормализованную цену/маршрут/ссылку/время/предупреждения;
- не продаёт билеты внутри приложения;
- не считает observation гарантией покупки;
- предназначен для редких ручных проверок, а не фонового массового polling.
```

---

## Самый важный итог

Не строить “ещё один fake Aviasales”. Строить честный self-host hunter:

```text
Aviasales Data API = широкий cached radar
RU click-out links = быстрый путь купить/проверить
Personal Browser Observer = редкая свежая проверка глазами/браузером пользователя
History + ranking + alerts = настоящая ценность проекта
```

Пользователь хочет “работало”. Значит приоритет у practical path:

- меньше теории;
- больше typed models;
- больше link builders;
- больше parser fixtures;
- больше visible browser observer;
- меньше заглушек;
- никаких fake live цен.
