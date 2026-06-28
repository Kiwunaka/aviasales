# Источники авиаданных и репозитории: состояние на 23 июня 2026

> Этот документ — техническое исследование, а не юридическое заключение. Перед включением любого провайдера в production необходимо повторно проверить договор, правила использования, квоты и допустимость фоновых запросов. Правила кодируются в `ProviderPolicy`, а не остаются только в документации.

## Главный вывод

Для частного приложения на несколько человек нельзя строить архитектуру вокруг real-time Search API Aviasales:

- новая версия Search API доступна проектам с подтверждёнными **50 000+ MAU**;
- каждый live-поиск должен быть инициирован действием пользователя;
- запрещены автоматический сбор результатов и объединение Search API с API других авиаметапоисков;
- старая версия Search API прекратила работу **15 июня 2026 года**.

Поэтому правильная архитектура разделяет источники на четыре класса:

1. **Cached / indicative discovery** — можно использовать для календарей, фонового мониторинга и предварительного отбора, если договор источника это разрешает.
2. **Live user-initiated search** — запускать только после явного действия пользователя, отдельно по провайдеру и в рамках его правил.
3. **Bookable airline distribution** — Duffel или иной поставщик контента, если аккаунт и договор разрешают нужный сценарий.
4. **Browser automation / scraping** — выключено по умолчанию, без обхода CAPTCHA, антибота, логина, геоблокировок и технических ограничений. Любой такой адаптер требует отдельного письменного разрешения или юридической проверки.

Итоговый продукт должен быть не «скрейпером Aviasales», а **provider-agnostic системой поиска, нормализации, анализа и оповещений**, где каждый адаптер имеет собственную политику выполнения.

---

## Матрица провайдеров

| Источник | Тип данных | Доступ | Фоновый мониторинг | Смешивание с другими источниками | Роль в продукте | Решение |
|---|---|---|---|---|---|---|
| Aviasales Data API | Кэшированные цены и направления | Travelpayouts token | Допустим как cached source при соблюдении правил и квот | Не считать live-выдачей; проверять текущий договор | Календарь, discovery, история, дешёвые даты | **Включить первым** |
| Aviasales Search API 2025+ | Real-time выдача | Только 50 000+ подтверждённых MAU | **Запрещён**: каждый поиск от пользователя | **Запрещено** объединять с API других метапоисков | Отдельный live-режим для будущего | **Адаптер реализовать, выключить** |
| Skyscanner Indicative Prices | Оценочные/агрегированные цены | Только после одобрения партнёрства | Предназначен для гибких запросов; точные условия — по договору | Только если договор разрешает | Гибкие даты, предварительный отбор | **Опциональный адаптер** |
| Skyscanner Live Prices | Real-time create/poll | Только после одобрения партнёрства | **Только user-generated** с точными датами | По договору | Live refresh по клику | **Опциональный, policy-gated** |
| Skyscanner MCP | Выбранные данные/функции для AI | Case-by-case | По индивидуальным условиям | По индивидуальным условиям | Возможный официальный agent-интерфейс | **Следить / запрашивать доступ** |
| Duffel Flights | Bookable offers от авиакомпаний | Аккаунт, test/live token и коммерческие условия | Не предполагать: задаётся договором и policy flag | Обычно это не метапоиск; всё равно проверять договор | Live offers, fare rules, будущая бронь | **Предпочтительный live-кандидат** |
| Amadeus Self-Service | Offers/search, ограничения по контенту | Self-Service/production contract | По условиям | По условиям | Только legacy/переходный источник | **Не делать стратегической зависимостью** |
| Airline direct APIs | Прямые предложения | Индивидуальные договоры | По договору | Обычно можно нормализовать, если разрешено | Лучшее качество и контроль | **Добавлять точечно** |
| OurAirports | Аэропорты и координаты | Public Domain CSV | Да | Да | Nearby airports, география | **Включить** |
| RSS/Atom/email/webhook deal feeds | Горящие предложения и рассылки | Публичный feed или разрешение пользователя | Да, если условия разрешают | Да | Дополнительный сигнал, не источник истины | **Включить через общий интерфейс** |
| Google Flights / Kayak / Skyscanner website scraping | Веб-страницы | Нет официального общего public fare API | Рискованно | Рискованно | Не использовать по умолчанию | **Запрещено без разрешения** |

---

## 1. Aviasales / Travelpayouts

### 1.1. Aviasales Data API — практичный старт

Официальная документация:

- https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits

Что важно:

- Доступ предоставляется по API token из профиля Travelpayouts.
- Это **не real-time поиск**. Данные берутся из кэша пользовательских поисков Aviasales и хранятся до 7 дней.
- `v3/prices_for_dates` возвращает найденные пользователями дешёвые билеты; для конкретных дат документация описывает предложения, найденные за последние 48 часов.
- Есть параметры рынка, валюты, дат, прямого рейса, числа пересадок и пагинации.
- Есть матрицы цен, альтернативные направления и статические словари.
- Для `v3/prices_for_dates` опубликован лимит 600 запросов в минуту, но продукт должен использовать собственный лимитер существенно ниже, кэш, jitter и заголовки `X-Rate-Limit-*`.
- Истёкшие цены нельзя выдавать как актуальные. UI обязан показывать источник, время получения, свежесть и необходимость live-проверки.

Роль в Flight Hunter:

- календарь ±3/±7 дней;
- первичный отбор направлений;
- фоновое построение собственной истории цен;
- поиск потенциально выгодных дат;
- генерация кандидатов для последующего live refresh;
- широкое сканирование «куда дёшево» в рамках пользовательского бюджета.

Не обещать пользователю, что цена гарантированно доступна. Формулировка: «последняя наблюдавшаяся цена; подтвердите перед покупкой».

### 1.2. Новый Aviasales Flight Search API

Официальная документация:

- https://support.travelpayouts.com/hc/en-us/articles/30565016140434-Aviasales-Flight-Search-API-real-time-and-multi-city-search
- https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- https://support.travelpayouts.com/hc/en-us/articles/34788165535250-Search-API-usage-rules

Критические ограничения:

- доступ только проектам с подтверждёнными 50 000+ MAU, без исключений для pre-launch;
- базовый лимит — 100 запросов в час с одного пользовательского IP;
- backend-only; требуется передавать реальный пользовательский IP и подпись;
- поиск запускается, затем результаты опрашиваются по `search_id`; сбор может занимать 30–60 секунд, URL результатов живёт 15 минут;
- поддерживается multi-city;
- каждый поиск должен быть вызван действием пользователя;
- выдача показывается пользователю полностью;
- booking link генерируется только после клика по кнопке покупки;
- запрещена автоматическая предварительная генерация booking links;
- запрещено автоматически собирать/скрейпить результаты Search API;
- запрещено объединять его выдачу с API других авиаметапоисков.

Архитектурное следствие:

- `AviasalesSearchAdapter` реализуется как отдельный модуль, но feature flag по умолчанию `false`;
- запрос требует одноразовый `UserActionGrant`, связанный с HTTP/Telegram action и сроком жизни;
- результаты хранятся только в пределах допустимого временного окна и не используются scheduler-ом;
- UI показывает отдельный provider workspace, а не общий merged ranking;
- booking redirect создаётся отдельным endpoint только после клика;
- policy guard технически блокирует background jobs и merge pipeline.

### 1.3. Старая версия Search API

Официальная страница:

- https://support.travelpayouts.com/hc/en-us/articles/203956173-Aviasales-Flights-Search-API-old-version

Страница указывает, что старая версия прекратила работу 15 июня 2026 года. Не использовать старые примеры, библиотеки и endpoints из блогов или репозиториев.

---

## 2. Skyscanner

Официальная документация:

- https://developers.skyscanner.net/docs/getting-started/authentication
- https://developers.skyscanner.net/docs/getting-started/usage-guidelines
- https://developers.skyscanner.net/docs/flights-live-prices/overview
- https://developers.skyscanner.net/docs/flights-indicative-prices/overview
- https://developers.skyscanner.net/docs/mcp-server

Что важно:

- API key выдаётся после рассмотрения заявки партнёрской командой.
- Live Prices использует create/poll workflow и возвращает bookable варианты.
- Usage Guidelines требуют, чтобы Live Pricing запускался только пользовательским запросом с точными origin, destination и датами.
- Для запросов без точных дат предлагается Indicative Prices API.
- Официальный MCP server уже существует, но доступ выдаётся case-by-case.
- Multi-city поддерживается в актуальной версии Live Prices, но конкретные лимиты и коммерческие правила нужно получать в партнёрском договоре.
- Старый `Skyscanner/skyscanner-python-sdk` архивирован и давно deprecated; не брать его за основу. Реализовать typed HTTP client по текущей спецификации или сгенерировать client из актуальной OpenAPI, если она предоставлена партнёру.

Архитектурное следствие:

- два разных адаптера: `SkyscannerIndicativeAdapter` и `SkyscannerLiveAdapter`;
- Live требует `UserActionGrant`;
- Indicative может участвовать в flexible-date planner только при разрешённой policy;
- официальный MCP рассматривается как дополнительный интерфейс, а не как обход требований к API key и партнёрству.

---

## 3. Duffel

Официальная документация:

- https://duffel.com/docs/api/v2/offer-requests
- https://duffel.com/docs/api/overview/test-mode
- https://duffel.com/docs/api/v2/offers

Сильные стороны:

- API проектировался для поиска и покупки авиапредложений, а не только для affiliate click-out;
- Offer Request принимает пассажиров, cabin class и slices маршрута;
- предложения содержат конкретные сегменты и цены;
- есть test mode;
- можно поддерживать split-ticket candidates и полноценные fare attributes, где это возвращает поставщик;
- цена и offer должны обновляться непосредственно перед покупкой, потому что offers имеют ограниченный срок жизни.

Ограничения:

- доступность авиакомпаний и рынков зависит от аккаунта и договора;
- автоматический мониторинг нельзя считать разрешённым только потому, что API технически доступен — нужен policy flag из договора;
- бронирование, платежи, возвраты и обслуживание заказа — отдельный большой контур. В первой полной версии Flight Hunter продукт остаётся search-and-redirect системой, а booking subsystem включается отдельным ADR и feature flag.

Решение:

- сделать `DuffelAdapter` production-grade с test fixtures и live feature flag;
- не хранить просроченные offers как «доступные»;
- хранить price snapshot и provenance отдельно от живого offer object;
- перед любым будущим purchase flow выполнять refresh/retrieve и показывать полные условия.

---

## 4. Amadeus

Официальные ресурсы:

- https://developers.amadeus.com/
- https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
- https://github.com/amadeus4dev/amadeus-python
- https://github.com/amadeus4dev/amadeus-flight-booking-django

На 23 июня 2026 официальный developer portal предупреждает о выводе Self-Service portal из эксплуатации 17 июля 2026 года. Поэтому новый продукт не должен зависеть от Self-Service как от стратегического поставщика. Допускается:

- legacy adapter для уже существующего аккаунта;
- Enterprise adapter после подтверждения актуальной программы и договора;
- использование официальных репозиториев только как примеров OAuth, моделей и booking flow, но не как гарантии долгосрочной доступности Self-Service.

---

## 5. География аэропортов

Официальный источник:

- https://ourairports.com/data/
- https://github.com/davidmegginson/ourairports-data

OurAirports публикует обновляемые каждую ночь CSV в Public Domain. Данные можно импортировать в PostgreSQL/PostGIS для:

- поиска аэропортов в радиусе 150 км;
- вычисления расстояния;
- metro-area grouping;
- отображения координат и типов аэропортов.

Источник прямо предупреждает, что не гарантирует точность. Поэтому:

- хранить `source_updated_at` и `verified_at`;
- разрешить admin override;
- не включать закрытые, военные, маленькие и нерелевантные аэродромы без фильтра;
- IATA city codes и коммерческую релевантность обогащать данными провайдера;
- расстояние до аэропорта — только один фактор: учитывать примерное время и стоимость наземного трансфера.

---

## 6. Что делать с парсингом сайтов

### Разрешённый стандарт продукта

Browser adapter может существовать только как интерфейс с такими состояниями:

- `disabled` — значение по умолчанию;
- `allowed_by_written_permission`;
- `allowed_by_public_terms`;
- `manual_user_session_only`;
- `blocked`.

Запрещено реализовывать:

- обход CAPTCHA;
- fingerprint spoofing;
- rotating/residential proxies для обхода блокировок;
- подделку геолокации или пользовательского IP;
- обход paywall/login/access control;
- скрытую автоматизацию действий пользователя;
- агрессивный polling;
- использование украденных cookies/tokens;
- автоматическое принятие условий от имени пользователя.

Playwright допускается для E2E-тестирования **собственного** web UI и для явно разрешённых browser integrations. Он не является базовым источником авиаданных.

---

## 7. Разбор найденных репозиториев

### affromero/flight-finder

- https://github.com/affromero/flight-finder

Плюсы:

- живой self-hosted проект;
- web UI, multi-user, PWA, история цен, графики, cron, PostgreSQL/Prisma, Docker;
- хороший пример onboarding, self-host install, share links и price-history UX.

Минусы:

- ключевой источник — Playwright scraping Google Flights;
- есть VPN routing, anti-detection, spoofing browser signals, experimental scraping Skyscanner/Kayak;
- это создаёт высокий ToS/operational risk.

Вердикт: **использовать только как UX/packaging reference**. Не переносить stealth, fingerprint spoofing, CAPTCHA/proxy обход и scraping pipeline.

### stufently/aviasales-mcp

- https://github.com/stufently/aviasales-mcp

Плюсы:

- компактный пример MCP tools поверх Travelpayouts Data API;
- поиск цен, календарь, направления и географические справочники;
- Python, Docker, тесты.

Минусы:

- небольшой проект, не полноценный продукт;
- Data API остаётся cached, а не live;
- нет multi-user, history model, policy engine и production observability.

Вердикт: **полезный reference для adapter/tool schemas**, но не база приложения.

### richarddanipog/flight-copilot

- https://github.com/richarddanipog/flight-copilot

Плюсы:

- FastAPI + React/Tailwind;
- provider abstraction;
- natural-language layer;
- понятное разделение backend/frontend.

Минусы:

- учебный масштаб;
- мало истории разработки;
- нет production scheduler, policy guard, durable price history и provider contracts.

Вердикт: **архитектурный эскиз, не production base**.

### rihua-tech/travelpayouts-flight-collector

- https://github.com/rihua-tech/travelpayouts-flight-collector

Плюсы:

- простой паттерн ежедневного ingestion Travelpayouts Data API;
- dated snapshots;
- тесты и automation.

Минусы:

- CSV collector, не приложение;
- нет нормализованной offer model, UI и alerts.

Вердикт: **reference для ingestion/snapshot job**.

### Pursuit2703/aviasales_tracker

- https://github.com/Pursuit2703/aviasales_tracker

Плюсы:

- Telegram bot;
- подписки, price threshold, фоновые проверки;
- простая модель команд.

Минусы:

- малый проект;
- слишком частый polling не должен копироваться без policy/rate limiter;
- SQLite и простая логика недостаточны для нормализации и дедупликации.

Вердикт: **reference для UX команд Telegram**, не кодовая база.

### Lookich39/AviaHunter

- https://github.com/Lookich39/AviaHunter

Плюсы:

- multi-user Telegram flow;
- origin/destination/date/max-price;
- периодические проверки.

Минусы:

- аналогично: маленький проект, без provider policy, полноценной истории и web UI.

Вердикт: **reference для bot conversation flow**.

### amadeus4dev/amadeus-python и amadeus-flight-booking-django

- https://github.com/amadeus4dev/amadeus-python
- https://github.com/amadeus4dev/amadeus-flight-booking-django

Плюсы:

- официальные примеры;
- полезны для понимания authentication и booking flow.

Минусы:

- Self-Service меняет статус в июле 2026;
- нельзя делать их фундаментом нового продукта без подтверждённой миграции/Enterprise contract.

### Skyscanner/skyscanner-python-sdk

- https://github.com/Skyscanner/skyscanner-python-sdk

Репозиторий архивирован и deprecated. **Не использовать**. Реализовать current API client по официальной документации.

---

## 8. Рекомендуемый порядок подключения

1. `OurAirportsAdapter` + Travelpayouts static dictionaries.
2. `AviasalesDataAdapter` для cached discovery и собственной истории.
3. `ManualOfferAdapter` и `DealFeedAdapter` для ссылок/RSS/email/webhook.
4. `DuffelAdapter` в test mode, затем live после коммерческого одобрения.
5. `SkyscannerIndicativeAdapter` и `SkyscannerLiveAdapter` после API approval.
6. `AviasalesSearchAdapter` реализован, но остаётся выключенным до достижения 50 000 MAU и письменного доступа.
7. Airline direct adapters — по одному, только при наличии официального API/договора.
8. Browser adapters — только после отдельного разрешения; никогда не обходить технические защиты.

---

## 9. Обязательные product labels

Каждая цена в UI и Telegram должна иметь:

- источник;
- `observed_at`;
- `expires_at`, если есть;
- freshness label: `LIVE`, `RECENT`, `CACHED`, `STALE`;
- валюту провайдера и нормализованную валюту;
- число пассажиров, включённый багаж и fare family, если известно;
- тип билета: single-PNR / self-transfer / split-ticket / hidden-city research;
- предупреждение, если цена требует повторной проверки;
- ссылку только по правилам соответствующего провайдера.

Никогда не называть cached цену «гарантированной» или «доступной сейчас» без live refresh.
