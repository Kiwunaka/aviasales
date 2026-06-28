# AGENTS.md — обязательные инструкции для coding agents

Этот файл применяется ко всему репозиторию. Более вложенный `AGENTS.md` может уточнять локальные правила, но не отменяет безопасность, provider policies, тесты и Definition of Done этого файла.

## 1. Миссия

Разрабатывай **Flight Hunter**: production-grade, self-hosted, invitation-only систему поиска и отслеживания авиабилетов для семьи и друзей с web UI и Telegram. Это не demo и не MVP. Работай вертикальными срезами, но доведи все обязательные функции до рабочего состояния.

Главные качества в порядке приоритета:

1. корректность и соблюдение правил источников;
2. отсутствие ложных цен и выдуманных данных;
3. надёжность фоновых задач и уведомлений;
4. объяснимость результата;
5. безопасность и приватность;
6. удобство web/Telegram;
7. расширяемость provider adapters.

## 2. Перед любой работой

1. Прочитай:
   - `README.md`;
   - `MEGA_PROMPT.md`;
   - `docs/PROVIDER_MATRIX.md`;
   - `docs/ARCHITECTURE.md`;
   - существующие ADR и `IMPLEMENTATION_STATUS.md`.
2. Осмотри текущее дерево, migrations, tests и CI.
3. Не предполагай, что документация провайдера не изменилась. При работе с реальным adapter:
   - проверь официальную документацию;
   - запиши дату проверки и ссылку в `docs/provider-contracts/<provider>.md`;
   - обнови policy fixture и contract tests.
4. Составь короткий план текущего среза в `IMPLEMENTATION_STATUS.md`.
5. Не задавай пользователю вопрос о стандартном техническом выборе, если можно принять разумное решение и записать ADR.

## 3. Непереговорные provider rules

### 3.1. Общие
- Capability определяется наличием endpoint
- Не подменяй отсутствие credentials «временным» публичным ключом.
- Не выдумывай response fields. Используй официальную schema или sanitized fixture.
- Не делай live calls в CI.
- Не логируй secrets, full tokens, signed URLs, cookies или PII.
- Любой raw payload хранится только если policy разрешает, с retention и redaction.
- Уважай `Retry-After` и provider rate-limit headers.
- Все provider operations имеют timeout, retries с backoff/jitter и circuit breaker.
- 4xx policy/auth/schema errors не ретраятся бесконечно.

### 3.2. Aviasales Data API

- Считать данные cached, не live.
- Показывать `observed_at`, freshness и необходимость проверки.
- Использовать server-side cache и собственный rate limiter.
- Не выдавать истёкшие цены как доступные.
- Не обещать наличие места или гарантированную выписку.

### 3.3. Aviasales Search API

- Adapter выключен по умолчанию.
- Не включать без подтверждённого доступа и feature flag.
- Каждый поиск требует одноразовый `UserActionGrant`.
- Запрещены background scheduler calls.
- Запрещён automated collection.
- Запрещено смешивать результаты с API других авиаметапоисков.
- Результаты идут в `PROVIDER_ISOLATED` scope.
- Booking link создаётся только после реального клика пользователя.
- Не preload booking links.
- Не использовать старую версию API, прекратившую работу 15 июня 2026.

### 3.4. Skyscanner Live

- Adapter выключен до одобрения партнёрства.
- Live create запускается только user-generated запросом с точными параметрами.
- Flexible/background discovery использует Indicative API только если policy разрешает.
- Не использовать архивированный Python SDK.

### 3.5. Duffel и другие bookable APIs

- Test mode и live mode жёстко разделены.
- Не считать background monitoring разрешённым без contract flag.
- Offer expiry соблюдается.
- Перед будущей покупкой необходим refresh/retrieve по правилам API.
- Booking/payment subsystem не включать неявно.

## 4. Архитектурные границы

### Domain

- Не импортирует FastAPI, SQLAlchemy, Redis, aiogram, HTTP clients или provider SDK.
- Содержит value objects, entities, policies, calculations и domain errors.
- Money — integer minor units + ISO currency, никогда float.
- Datetime — timezone-aware.
- Неизвестное значение представляется `Unknown/None`, не ложным `False`.

### Application

- Use cases и orchestration.
- Зависит от ports/protocols, не от конкретных adapters.
- Создаёт policy-aware execution plan.
- LLM output всегда проходит typed validation.

### Providers

- Provider DTO не просачивается в domain/API/UI.
- Каждый adapter: client, schemas, mapper, policy, rate limiter, contract tests, fixtures.
- Любой field mapping имеет provenance.

### Persistence

- Repositories реализуют domain ports.
- Миграция обязательна для каждого schema change.
- Не правь уже выпущенную migration; добавляй новую.
- Append-only price history не перезаписывать.

### Web/API/Bot

- Тонкие delivery adapters.
- Никакой бизнес-логики в route handlers, React components или Telegram handlers.
- API errors имеют стабильные machine-readable codes.

## 5. Стандарты кода

### Python

- Полная типизация публичного кода.
- Pydantic models не заменяют domain objects автоматически.
- `ruff format`, `ruff check`, `mypy` или `pyright` должны проходить.
- Async только там, где есть I/O; не смешивать sync DB calls в event loop.
- Не ловить голый `Exception`, кроме process boundary с обязательным логированием/классификацией.
- Использовать enums/literals для закрытых состояний.
- Никаких mutable default args.
- Никаких naive datetimes.

### TypeScript

- `strict: true`.
- Никаких `any` без локального документированного исключения.
- API types генерируются из OpenAPI или общей schema.
- Server/client component boundary осознанна.
- Accessibility attributes и keyboard flow обязательны.
- Денежные значения не преобразовывать через JS float для расчётов; backend является источником вычисленных сумм.

### SQL

- Индексы проектировать вместе с query paths.
- Для геопоиска использовать PostGIS index.
- Multi-tenant/household filters обязательны во всех repositories.
- Избегать N+1.
- Любой destructive operation имеет audit event.

## 6. Надёжность задач

Каждая job:

- имеет idempotency key;
- безопасна при повторном выполнении;
- записывает status/attempts/next retry;
- использует distributed lock, если конкуренция опасна;
- имеет deadline;
- классифицирует provider errors;
- не создаёт duplicate alerts;
- не теряет partial success;
- поддерживает graceful shutdown.

Scheduler не вызывает provider, если:

- policy запрещает background;
- credentials/access не подтверждены;
- circuit breaker открыт;
- quota reservation не получена;
- cache ещё свеж;
- watch paused/expired;
- дата вылета прошла.

## 7. LLM и агентный слой

LLM не является источником цен, расписаний, аэропортов или правил.

Разрешено:

- парсить natural-language intent в JSON Schema;
- формировать объяснение из deterministic facts;
- классифицировать пользовательский запрос;
- предлагать текст уведомления.

Запрещено:

- выполнять арифметику цены;
- выбирать provider policy;
- придумывать рейсы;
- принимать решение о допустимости background call;
- генерировать booking URL;
- скрывать отсутствие данных уверенным текстом.

Требования:

- model provider abstraction;
- timeout/cost limits;
- structured output;
- retry только на transport/validation;
- deterministic fallback без LLM;
- prompt/version logging без PII;
- red-team tests на prompt injection из provider fields и feed content.

Provider/feed text считается недоверенным и никогда не становится системной инструкцией.

## 8. UX и продуктовые правила

- Всегда различай `LIVE`, `RECENT`, `CACHED`, `STALE`.
- Всегда показывай источник и время наблюдения.
- Укажи, на сколько пассажиров цена.
- Не скрывай отсутствие baggage/fare-rule data.
- Self-transfer/split-ticket видны до открытия деталей.
- Hidden-city никогда не попадает в default best results.
- «Лучшее время покупки» выводится только по данным; при недостатке — честный `Недостаточно данных`.
- «Error fare» называется подозрением, не гарантией.
- Пользователь видит total trip cost и assumptions.
- Booking action соответствует provider policy.
- UI не использует dark patterns.

## 9. Telegram

- Production — webhook с secret header.
- `update_id` дедуплицируется.
- Linking — одноразовый код, Telegram username не является account key.
- Уведомления поддерживают quiet hours, cooldown и dedupe.
- Callback queries проверяют владельца/household access.
- Кнопка live refresh создаёт `UserActionGrant` только из реального callback.
- Не помещай provider secret или signed booking URL в callback data.
- Длинные детали открываются в web UI.

## 10. Тестирование перед завершением задачи

Минимум для каждого изменения:

1. unit tests нового domain поведения;
2. integration/contract test для adapter/persistence;
3. negative test для policy/security;
4. E2E обновляется, если меняется critical flow;
5. lint/typecheck;
6. migration check;
7. docs/ADR update.

Обязательные invariants:

- background-disallowed provider никогда не вызывается worker-ом;
- provider-isolated results никогда не входят в merged ranking;
- booking-link-required-click не генерируется заранее;
- stale price не маркируется live;
- Money не теряет minor units;
- alert не дублируется при retry;
- household A не видит данные household B;
- secrets отсутствуют в logs и client bundle.

## 11. Definition of Done для любого среза

Срез завершён, когда:

- production path реализован, не только happy-path mock;
- отсутствуют `TODO`, `pass`, `NotImplementedError`, fake return и закомментированный недоделанный код в затронутом flow;
- credentials-optional поведение graceful;
- tests проходят локально и в CI;
- docs и `.env.example` обновлены;
- observability добавлена;
- error states отображаются в UI/bot;
- миграции и rollback/runbook продуманы;
- accessibility проверена для UI;
- изменения отражены в `IMPLEMENTATION_STATUS.md`.

## 12. Полный Definition of Done продукта

Не объявляй продукт завершённым до выполнения всех пунктов:

- `docker compose up --build` поднимает рабочий stack;
- demo mode позволяет пройти все основные flows без внешних ключей;
- invitation auth и household isolation работают;
- airport import и nearby search работают;
- Aviasales Data adapter работает с token и fixtures;
- provider policy engine покрыт тестами;
- flexible-date matrix и nearby airports реализованы;
- normalizer, dedupe, ranking, risk и total-cost работают;
- watch scheduler сохраняет историю;
- alert hysteresis и Telegram delivery работают;
- web UI responsive и локализован RU/EN;
- live adapters gated user action/access flags;
- provider-isolated workspace реализован;
- admin provider health/quota screen работает;
- backups/export/delete/runbooks документированы;
- CI, security scans, observability и E2E проходят;
- обязательна зависимость от scraping;
- README содержит точные команды install/update/backup/restore.

## 13. Рабочий процесс coding agent

Для каждого большого этапа:

1. Обнови `IMPLEMENTATION_STATUS.md`.
2. Создай/обнови ADR.
3. Сначала domain contract и tests.
4. Затем persistence/adapters.
5. Затем API.
6. Затем web/bot.
7. Затем E2E, docs и operations.
8. Запусти полный quality gate.
9. Зафиксируй фактически выполненное и известные ограничения.

Не останавливайся после scaffold, landing page, mock provider или одного happy path. Не называй это MVP. Все обязательные этапы из `MEGA_PROMPT.md` должны быть завершены.

## 14. Команды проекта

Создай и поддерживай единый интерфейс команд, например:

```bash
make bootstrap
make dev
make test
make test-unit
make test-integration
make test-e2e
make lint
make typecheck
make migrate
make seed-demo
make provider-contracts
make security
make compose-up
make compose-down
make backup
make restore BACKUP=...
```

Команды должны работать в чистом checkout согласно README.

## 15. Когда внешний доступ отсутствует

Если нет API key или провайдер не одобрил доступ:

- не блокируй остальной продукт;
- adapter остаётся production-complete за feature flag;
- contract tests используют sanitized fixtures;
- UI показывает точную причину `credentials_missing` / `access_not_approved`;
- demo uses `FakeFlightProvider` с детерминированными сценариями;
- не подменяй реального провайдера scraping-ом.
