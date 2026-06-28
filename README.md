# Flight Hunter

Семейный self-hosted поиск и отслеживание авиабилетов.

Главное: проект не обещает “живые” цены там, где источник даёт только кэш. Он честно показывает источник, свежесть и ограничения.

## Начать отсюда

Если вы не разработчик или просто хотите без лишней магии, откройте:

**[docs/START_HERE_RU.md](docs/START_HERE_RU.md)**

Там коротко:

- что уже можно запустить;
- какие команды копировать;
- что мне нужно от вас;
- где взять Telegram bot token и Travelpayouts token;
- что можно не трогать прямо сейчас.

## Что уже работает

Сейчас реализована backend-demo основа и простой web-экран без внешних ключей:

- web-страница `GET /` с chat-first агентом, формой поиска, источниками и результатами;
- provider policy guard;
- SearchIntent/API model with explicit passenger mix and trip type validation;
- demo search через `FakeFlightProvider`;
- Aviasales Data adapter, включаемый через `.env`;
- список providers и причины, почему реальные sources выключены;
- source contract catalog `GET /api/v1/source-contracts`: показывает readiness каждого источника
  (`implemented`, `policy_skeleton`, `contract_only`), env flags, adapter module, policy
  invariants и blocked reasons без раскрытия secrets;
- airport autocomplete, city-name search и nearby airports: demo-набор работает сразу,
  SQLite-compatible OurAirports import доступен через локальный CSV;
- flexible date matrix без provider calls;
- ранжирование mergeable результатов с видимыми caveats;
- alert hysteresis/dedupe logic;
- Telegram webhook security foundation: secret header and durable `update_id` dedupe;
- первый слой базы: Alembic migrations, household-isolated watches, price history и alert dedupe;
- Watch API: создать/list watches с household isolation через временные headers;
- admin provider health endpoint без раскрытия secrets;
- agent chat API: typed turn endpoint, airport choices, safe action cards, watch creation only
  after explicit "следи/мониторь/уведомляй" wording, and audit without raw chat storage;
- optional Codex CLI intent bridge skeleton: выключен по умолчанию, sandbox/read-only/schema-gated,
  не является источником цен, рейсов или provider policy;
- optional OpenAI Responses agent backend: выключен по умолчанию, включается только через
  `AGENT_OPENAI_ENABLED=true` + `OPENAI_API_KEY`, возвращает typed intent draft/schema output,
  не получает provider secrets и не выполняет live/browser calls;
- agent presets API: безопасные сценарии "когда покупать", даты +/- 3 дня,
  аэропорты рядом, hidden-city, split ticket, error fare и валюта/страна сайта;
- live refresh gate: будущие live-проверки не чаще одного раза в 10 минут и только
  после явного действия пользователя;
- live observation control plane: каталог browser sources, одноразовые grants,
  idempotent create endpoint и fake worker без внешних live-вызовов;
- durable live observation storage and retention cleanup for short-lived grants/results/idempotency;
- price source catalog: RUB-first источники без брони в приложении, с покупкой
  через внешний click-out;
- scraping observer policy: рискованный future-режим выключен по умолчанию и
  запрещает CAPTCHA/stealth/proxy/cookie обходы;
- Aviasales Search API и MCP policy skeletons: выключены по умолчанию, требуют
  user-action policy и typed validation перед будущими интеграциями;
- unit tests, lint и typecheck.

## Быстрый запуск demo API

Нужно только `uv`.

```powershell
uv sync --group dev
uv run uvicorn flight_hunter.api.app:app --reload --host 127.0.0.1 --port 8000
```

Откройте:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/healthz
- http://127.0.0.1:8000/docs

## Проверка проекта

```powershell
uv run pytest tests/unit
uv run ruff format --check .
uv run ruff check .
uv run mypy
```

Применить текущие миграции к локальной demo SQLite базе:

```powershell
uv run alembic upgrade head
```

Проверить Travelpayouts/Aviasales Data token одним безопасным cached-запросом:

```powershell
uv run travelpayouts-smoke
```

Команда печатает только summary, без token, booking links и raw payload.

Сделать backup/restore локальной demo SQLite базы:

```powershell
uv run flight-hunter-backup
uv run flight-hunter-restore .\backups\ИМЯ_BACKUP.db
uv run flight-hunter-cleanup-live-observations --dry-run
```

Импортировать локальный OurAirports `airports.csv` в demo SQLite:

```powershell
uv run flight-hunter-import-airports --airports-csv .\data\airports.csv
```

Последний проверенный результат:

```text
168 passed
ruff format/check passed
mypy passed
migration upgraded through 0006
```

## Что пока не готово

Пока нет полноценного PWA/Next.js UI, Telegram delivery queue, worker process, Docker Compose production stack и большинства live/bookable provider adapters.
Реализован первый реальный provider adapter: Aviasales Data API, с cached-семантикой и выключением по умолчанию.
Остальные источники теперь явно отражены в source contract catalog как `policy_skeleton` или
`contract_only`, а не замаскированы под рабочие интеграции.

Scraping, CAPTCHA bypass, stealth, fingerprint spoofing и rotating proxies не используются.

Live-цены не парсятся "втихую" со страниц агрегаторов. Для них нужен официальный
API/партнерский доступ, включенный provider adapter и пользовательское действие.
Если источник дает только cached данные, интерфейс обязан показывать cached/stale,
а не называть это live.
