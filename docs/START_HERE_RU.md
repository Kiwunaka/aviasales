# Flight Hunter: старт без техномагии

Эта страница для нормального человеческого запуска. Без “подними кластер”, “сконфигурируй всё на свете” и прочего тумана.

## Коротко

Сейчас можно запустить demo API без ключей и аккаунтов.

Для этого нужен только `uv`, менеджер Python-проектов.

## Что установить

### 1. uv

Официальная установка для Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Проверить:

```powershell
uv --version
```

Источник: https://docs.astral.sh/uv/

### 2. Python отдельно ставить обычно не надо

`uv` сам скачает подходящий Python для проекта.

Если хотите поставить руками: https://www.python.org/downloads/

## Как запустить то, что уже есть

Откройте PowerShell в папке проекта:

```powershell
cd "C:\Users\kiwun\Документы\CHEAP AIR FLY"
```

Установите зависимости:

```powershell
uv sync --group dev
```

Если хотите создать локальную demo-базу:

```powershell
uv run alembic upgrade head
```

Backup локальной demo-базы:

```powershell
uv run flight-hunter-backup
```

Restore из backup-файла:

```powershell
uv run flight-hunter-restore .\backups\ИМЯ_BACKUP.db
```

Посмотреть, сколько истекших live-check записей будет очищено:

```powershell
uv run flight-hunter-cleanup-live-observations --dry-run
```

Если у вас есть локальный OurAirports `airports.csv`, импортируйте справочник:

```powershell
uv run flight-hunter-import-airports --airports-csv .\data\airports.csv
```

Файл берётся локально. Команда не скачивает данные сама, не требует API key и пишет
только справочник аэропортов/статус импорта.

Запустите demo API:

```powershell
uv run uvicorn flight_hunter.api.app:app --reload --host 127.0.0.1 --port 8000
```

Откройте в браузере:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/healthz
- http://127.0.0.1:8000/docs

`/` — экран с чатом агента, формой поиска, источниками и результатами.

`/docs` — техническая страница, где можно нажимать API руками.

## Что попробовать в `/docs`

### Проверить, что сервер жив

Откройте `GET /healthz`.

Ожидаемый смысл ответа: `status: ok`.

### Посмотреть источники

Откройте `GET /api/v1/providers`.

Вы увидите:

- `fake` включён;
- реальные источники выключены;
- рядом показано, почему они выключены.

Это нормально. Без ключей проект всё равно работает в demo mode.

### Сделать demo-поиск

Откройте `POST /api/v1/searches` и вставьте:

```json
{
  "origin": "WAW",
  "destination": "BCN",
  "departure_date": "2026-10-12",
  "return_date": "2026-10-19",
  "passengers": 2,
  "currency": "PLN"
}
```

Важно: это demo-результат от `FakeFlightProvider`. Он нужен, чтобы проверить логику приложения без внешних ключей. Он не выдаётся за реальную цену.

### Проверить соседние аэропорты

Откройте:

```text
GET /api/v1/airports/nearby?iata_code=WAW&radius_km=150
```

Проект покажет расстояния, но не будет говорить “вы сэкономите”. Расстояние — это только факт, не обещание цены.

### Попробовать чат агента

Откройте `/` и напишите:

```text
из Варшавы в Барселону 2026-10-12 2026-10-19 следи
```

Агент покажет варианты аэропортов, безопасные действия, даты +/- 3 дня и создаст
watch только потому, что в фразе явно есть просьба следить. Live-проверка всё равно
остаётся отдельной кнопкой.

## Что мне нужно от вас

### Сейчас, чтобы продолжать разработку

Ничего обязательного.

Я могу продолжать строить demo mode, базу, web UI, Telegram-заглушку, scheduler и тесты без ваших внешних ключей.

### Когда захотите реальные cached-цены Aviasales Data API

Нужны:

- аккаунт Travelpayouts;
- API token;
- marker, если хотите affiliate/click-out сценарии позже.

Где взять token:

1. Зайдите в Travelpayouts.
2. Откройте профиль.
3. Откройте вкладку API token.

Официальная инструкция: https://support.travelpayouts.com/hc/en-us/articles/13024069738386-Where-to-find-API-token

Потом вы дадите значения для:

```env
TRAVELPAYOUTS_API_TOKEN=...
TRAVELPAYOUTS_MARKER=...
AVIASALES_DATA_ENABLED=true
```

Не присылайте ключи в чат, если не уверены. Лучше вставлять их локально в `.env`.

Локально это выглядит так:

```powershell
Copy-Item .env.example .env
notepad .env
```

В `.env` поменяйте только эти строки:

```env
AVIASALES_DATA_ENABLED=true
TRAVELPAYOUTS_API_TOKEN=ВАШ_TOKEN
```

`TRAVELPAYOUTS_MARKER` можно оставить пустым на текущем этапе.

После этого перезапустите demo API. В `GET /api/v1/providers` источник `aviasales_data` должен стать включённым.

Если token уже отправлялся в чат или чужой сервис, лучше потом перевыпустить его в Travelpayouts.

Проверить token одним безопасным cached-запросом:

```powershell
uv run travelpayouts-smoke
```

Команда не печатает token, booking links или raw payload. Она показывает только `ok`, код результата, количество найденных cached-записей и время ответа.

### Когда захотите Telegram-бота

Нужны:

- Telegram bot token;
- имя бота;
- позже — публичный HTTPS URL для webhook, если это production.

Где взять bot token:

1. В Telegram откройте `@BotFather`.
2. Напишите `/newbot`.
3. Следуйте шагам.
4. Сохраните token.

Официальная инструкция Telegram: https://core.telegram.org/bots/tutorial

Потом значения пойдут в:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=...
TELEGRAM_WEBHOOK_SECRET=...
```

Для локальной разработки можно оставить Telegram выключенным.

### Когда дойдём до self-hosted production

Понадобятся:

- домен, например `flights.example.com`;
- VPS или домашний сервер;
- email владельца для первого admin-аккаунта;
- сильные секреты для приложения;
- решение, нужны ли Telegram alerts сразу.

Секрет можно сгенерировать так:

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Что можно не трогать

Пока не нужны:

- Skyscanner;
- Duffel;
- Aviasales Search API;
- OpenAI/LLM key;
- scraping;
- proxies;
- Kubernetes.

Aviasales Search API отдельно ограничен: он требует подтверждённый доступ и не подходит для фонового сбора. Поэтому он выключен по умолчанию.

## Agent mode без магии

Сейчас агентный режим работает как typed chat-orchestrator и набор понятных
пресетов, а не как бот, который сам парсит сайты:

- чатовый turn endpoint понимает простые фразы с городами/датами;
- города резолвятся в варианты аэропортов, неоднозначность не угадывается;
- watch создаётся только по явной просьбе “следи/мониторь/уведомляй”;
- когда покупать;
- даты вылета +/- 3 дня;
- аэропорты рядом в радиусе 150 км;
- hidden-city только как отдельный рискованный режим;
- split ticket с предупреждением про самостоятельную пересадку;
- error fare источники после актуальной проверки;
- страна сайта авиакомпании и валюта оплаты.

Попробовать можно в `/docs`:

- `POST /api/v1/agent/chat/turn`;
- `GET /api/v1/airports/search?q=Варшава`;
- `GET /api/v1/agent/presets`;
- `POST /api/v1/agent/plan`.

Для этого не нужен OpenAI key, Codex OAuth или MCP server. По умолчанию стоит
`AGENT_PROVIDER=deterministic_presets`, `AGENT_CODEX_CLI_ENABLED=false` и
`AGENT_OPENAI_ENABLED=false`.

Если нужен OpenAI-backed агент для разбора естественного языка, включайте его отдельно:

- `OPENAI_API_KEY=...`;
- `AGENT_OPENAI_ENABLED=true`;
- `AGENT_OPENAI_MODEL=gpt-5.5`;
- понимание, что OpenAI output проходит typed validation и не может быть источником цен,
  расписаний, provider policy или live-проверок.

Если нужен локальный агент через Codex CLI, включайте его отдельно:

- установленный Codex CLI;
- исправный `~/.codex/config.toml` (`service_tier` должен быть `fast` или `flex`);
- `AGENT_CODEX_CLI_ENABLED=true`;
- понимание, что Codex output проходит typed validation и не может быть источником цен.

Live-цены агент сам не собирает. Он может предложить кнопку "обновить live", но
такая проверка идет не чаще одного раза в 10 минут:

```env
LIVE_REFRESH_MIN_GAP_SECONDS=600
```

## Откуда брать live-цены

Нормальный путь: официальные API и партнерские доступы.

- Travelpayouts/Aviasales Data API - cached цены, не live.
- Aviasales Search API - live, но только после подтвержденного доступа и действия пользователя.
- Skyscanner Live, Duffel, Amadeus/NDC - только после официального доступа и проверки правил.

Парсить страницы агрегаторов или авиакомпаний можно только если это явно разрешено
их правилами. В проекте не используются CAPTCHA bypass, stealth, fingerprint
spoofing, rotating proxies, чужие cookies или обход геолокации.

## Текущая модель для RUB и покупки снаружи

Покупки внутри приложения не будет. Flight Hunter ищет и объясняет цены, а покупать
пользователь идет наружу:

- Aviasales / Travelpayouts Data API - cached цена внутри приложения;
- Aviasales, Яндекс Путешествия, Туту, OneTwoTrip - click-out на внешний поиск;
- Аэрофлот, Победа, S7 и другие перевозчики - click-out на официальный сайт;
- финальная цена всегда подтверждается снаружи перед покупкой.

В API это видно здесь:

```text
GET /api/v1/price-sources
```

Scraping observer можно будет включать только точечно:

```env
SCRAPING_OBSERVER_ENABLED=false
SCRAPING_MIN_GAP_SECONDS=600
```

Даже если режим включить, он не будет делать CAPTCHA solving, stealth,
fingerprint spoofing, proxy rotation, использовать чужие cookies или закрытые
страницы. Такие цены будут называться `observed_price`, а не гарантированной
доступностью билета.

## Простая карта проекта

```text
src/flight_hunter/api            HTTP endpoints
src/flight_hunter/application    сценарии приложения
src/flight_hunter/domain         чистые правила и объекты
src/flight_hunter/geo            аэропорты и расстояния
src/flight_hunter/policy         правила provider calls
src/flight_hunter/providers      источники данных
src/flight_hunter/notifications  alert logic
tests/unit                       проверки
docs/adr                         решения по архитектуре
```

## Если что-то сломалось

### `uv` не найден

Закройте и заново откройте PowerShell. Потом:

```powershell
uv --version
```

### Порт 8000 занят

Запустите на другом порту:

```powershell
uv run uvicorn flight_hunter.api.app:app --reload --host 127.0.0.1 --port 8001
```

Откройте http://127.0.0.1:8001/docs

### Не хочется разбираться с API

Откройте http://127.0.0.1:8000/ — там уже есть простая форма поиска, список источников и результаты.
