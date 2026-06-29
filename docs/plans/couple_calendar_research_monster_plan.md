# МЕГА МОНСТР ПЛАН: довести couple-calendar research до идеала

> Формат: один цельный инженерный бэклог без дробления на фазы.
> Цель: сделать поиск/ресерч/агентов не генератором красивого мусора, а доказательным приватным планировщиком выходных для пары.

---

## 0. Целевое поведение продукта

Пользователь пишет что-то вроде:

```txt
хочу в выходные спокойную экотропу рядом с СПб, без жести, с красивыми фотками
```

Система **не должна**:

- отдавать рекламные подборки;
- отдавать KudaGo-спам;
- отдавать сниппеты из SearXNG/CRW как готовые места;
- придумывать часы, цены, маршруты, адреса, даты;
- называть “проверенным” то, что просто совпало по тексту;
- молча падать в локальный KudaGo fallback и делать вид, что работает полноценный агент;
- показывать 5 слабых вариантов только ради заполнения экрана.

Система **должна**:

- понять интент: еда, природа, событие, прогулка, indoor/outdoor, низкая/средняя энергия;
- найти сырых кандидатов;
- открыть источники;
- извлечь факты;
- проверить регион, дату, дорогу, цену, часы, сезонность;
- выкинуть мусор;
- показать 3–7 честных вариантов;
- для каждого варианта явно сказать, что проверено, что не проверено, что надо открыть руками перед поездкой;
- сохранить идею;
- предложить жене;
- после посещения сохранить фотоотчёт, заметки и предпочтения пары.

Главная формула:

```txt
Не “агент должен быть умнее”.
А “агент не должен получать мусор как будто это уже карточки”.
```

---

## 1. Главный принцип архитектуры поиска

В код надо вбить железное правило:

```txt
SERP ≠ карточка.
Aggregator ≠ проверенный факт.
Model rerank ≠ фактчек.
Score ≠ verification.
```

Сейчас часть проблемы в том, что CRW/SearXNG и KudaGo слишком рано превращаются в `AiSearchCard`. Потом модель получает уже “готовые карточки” и выбирает среди них, хотя часть результатов должна была остаться только сырыми кандидатами или источниками.

Правильная цепочка:

```txt
User query
→ normalize intent
→ generate source-specific queries
→ collect RawCandidate
→ dedupe candidates
→ open top sources
→ extract EvidenceFact
→ cross-check facts
→ score/rank
→ reject weak candidates
→ build AiSearchCard
→ model rerank only existing cards
→ UI shows verified / partially_verified / needs_check / missing facts
```

Запрещённые прямые переходы:

```txt
CRW result → AiSearchCard
KudaGo result → verified card
LLM idea → saved idea
SERP snippet → final result
High score → verified
```

---

## 2. Жёсткие инварианты качества

Эти правила должны быть одновременно в коде, тестах и prompt-контрактах:

```txt
1. Финальная карточка не создаётся из одного search snippet.
2. CRW/SearXNG имеет право находить URL, но не имеет права сам создавать финальную карточку.
3. KudaGo имеет право создавать event-candidate, но не verified-card без проверки даты/места/источника.
4. verified ставится только на основании evidence, а не высокого score.
5. Модель не имеет права создавать новые title/url/address/price/hours.
6. Модель имеет право выкинуть карточку, и код обязан это уважать.
7. Rejected-карточки нельзя добавлять обратно “в хвост”.
8. Deep research обязан открывать страницы, а не только rerank’ить найденное.
9. У каждой карточки должен быть список missingFacts.
10. У каждого результата должен быть checkedAt и source freshness.
11. Если nanobot/sidecar/crawl4ai недоступны, UI должен показывать degraded mode.
12. Лучше честное “ничего нормального не нашёл”, чем 5 мусорных идей.
```

---

## 3. Обнаруженные баги и точечные правки

| Место | Проблема | Что сделать |
|---|---|---|
| `server/src/agent/calendarAgentClient.ts` | При недоступном nanobot включается `FallbackCalendarAgentClient`, который уходит в локальный KudaGo/demo fallback. Можно думать, что работает агент, хотя работает старый режим. | Сделать явный `provider: degraded:local-kudago-fallback`, показать предупреждение в UI, не смешивать с нормальным поиском. |
| `server/src/ai/researchAgent.ts` | Старый fallback почти целиком KudaGo; в production при ошибке возвращает пусто, в dev — demo-карточки. | Оставить только аварийным режимом. Не использовать для нормального поиска. |
| `calendar-nanobot/src/providerRouter.ts` | `searchMode: deep` в `/api/ai/search` не делает live deep research: Codex запускается с `web_search="disabled"` и только rerank’ит готовые карточки. | Переименовать это в `rerank`, а настоящий deep отправлять через `/api/ai/research-jobs`. |
| `calendar-nanobot/src/providerRouter.ts` | `applyCardAdvice()` добавляет обратно карточки, которые модель не выбрала. | Возвращать только `advised`, если они есть. Не добавлять leftovers. |
| `calendar-nanobot/src/researchTools.ts` | `searchCrw()` делает финальные cards из SERP/snippets. | CRW должен возвращать только `sources`/`RawCandidate`, не `AiSearchCard`. |
| `calendar-nanobot/src/researchTools.ts` | `searchKudaGo()` не фильтрует событие по нужной дате, хотя `expand=place,dates` запрошен. | Фильтровать `dates` относительно `input.date`; без даты — `needs_check`, не verified. |
| `calendar-nanobot/src/researchTools.ts` | `ecoTrails` фактически завязан на `sourceSettings.crw`, хотя это отдельный источник. | Добавить отдельный source toggle `ecoTrails`. |
| `calendar-nanobot/src/researchTools.ts` | Домашняя точка захардкожена как `60.083597, 30.342875`, а preference `home_address` не используется для маршрутов. | Геокодировать `home_address`, кэшировать координаты, использовать в sidecar/nanobot. |
| `research-sidecar/app.py` | `score >= 80` превращается в `verification: verified`. Это неверно: score — ранжирование, не проверка. | Разделить `rankScore` и `verificationStatus`. |
| `research-sidecar/app.py` | `max_runtime_seconds` передаётся, но pipeline фактически не останавливает циклы по этому бюджету. | Ввести deadline object и проверять его перед search/open/extract/scoring. |
| `research-sidecar/app.py` | `search_kudago()` хардкодит `location: "spb"`. | Использовать city → KudaGo location mapping. |
| `research-sidecar/app.py` | `candidates_from_pages()` в основном берёт title и большой excerpt, а не структурные факты. | Добавить structured extractor: адрес, часы, цена, дата, координаты, маршрут, сезонность, evidence. |
| `server/src/routes.ts` | При создании research run сохраняются query/city/radius, но дата из запроса не сохраняется в run. | Добавить `date`, `searchMode`, `intent`, `sourceSettingsSnapshot` в research run. |
| `docker-compose.selfhost.yml` | `crawl4ai` стоит как `latest`. | Зафиксировать версию образа, добавить healthcheck, токен и лимиты. |
| `src/components/AgentAdminPanel.tsx` | Админка показывает 2GIS/CRW/KudaGo/OSM/Codex, но не показывает sidecar/crawl4ai/ecoTrails. | Добавить статусы: sidecar, crawl4ai, ecoTrails, fallback/degraded. |

---

## 4. Новый data contract

Сейчас `AiSearchCard` используется слишком рано. Нужно ввести промежуточные сущности.

```ts
type RawCandidate = {
  id: string;
  query: string;
  title: string;
  url: string;
  sourceName: string;
  sourceKind:
    | 'search_result'
    | 'aggregator'
    | 'map'
    | 'official'
    | 'catalog'
    | 'review'
    | 'index';
  snippet?: string;
  discoveredAt: string;
};

type OpenedSource = {
  candidateId: string;
  url: string;
  finalUrl: string;
  httpStatus?: number;
  title: string;
  text: string;
  markdown?: string;
  sourceName: string;
  openedBy: 'crawl4ai' | 'direct_http' | 'manual_index';
  checkedAt: string;
  contentHash: string;
};

type EvidenceFact = {
  candidateId: string;
  field:
    | 'existence'
    | 'official_url'
    | 'address'
    | 'coordinates'
    | 'opening_hours'
    | 'price'
    | 'date'
    | 'duration'
    | 'route'
    | 'parking'
    | 'public_transport'
    | 'seasonality'
    | 'reviews'
    | 'photos'
    | 'rules';
  value: string;
  sourceUrl: string;
  sourceName: string;
  trustTier: 'official' | 'map' | 'catalog' | 'aggregator' | 'review' | 'search';
  confidence: 'low' | 'medium' | 'high';
  checkedAt: string;
};

type VerificationReport = {
  candidateId: string;
  rankScore: number;
  verificationStatus: 'verified' | 'partially_verified' | 'needs_check' | 'rejected';
  confidence: {
    existence: 'unknown' | 'low' | 'medium' | 'high';
    address: 'unknown' | 'low' | 'medium' | 'high';
    hours: 'unknown' | 'low' | 'medium' | 'high';
    price: 'unknown' | 'low' | 'medium' | 'high';
    date: 'unknown' | 'low' | 'medium' | 'high';
    route: 'unknown' | 'low' | 'medium' | 'high';
    overall: 'low' | 'medium' | 'high';
  };
  missingFacts: string[];
  conflicts: Array<{
    field: string;
    values: string[];
    sources: string[];
  }>;
  rejectionReason?: string;
};
```

`AiSearchCard` должен появляться только после `VerificationReport`.

Расширить `AiSearchCard` или добавить companion-поле в API:

```ts
type ActivityVerificationMeta = {
  verificationStatus: 'verified' | 'partially_verified' | 'needs_check';
  confidence: VerificationReport['confidence'];
  missingFacts: string[];
  facts: EvidenceFact[];
  conflicts: VerificationReport['conflicts'];
};
```

---

## 5. Quick search: целевое поведение

`/api/ai/search` должен быть быстрым, но чистым.

Правила по интенту:

```txt
food:
  1. 2GIS first
  2. OSM fallback
  3. CRW only as sources, not cards

nature:
  1. eco-trails
  2. Overpass
  3. OSM
  4. CRW only as sources, not cards

events:
  1. KudaGo as event candidates
  2. date filter required
  3. source page/opened evidence required for higher confidence

generic:
  1. map/catalog sources first
  2. web sources only after opening
```

Quick search может вернуть `needs_check`, но не должен врать.

Пример нормальной карточки:

```json
{
  "title": "Экотропа Комаровский берег",
  "verification": "needs_check",
  "confidence": {
    "existence": "high",
    "route": "medium",
    "hours": "unknown",
    "price": "unknown"
  },
  "missingFacts": ["точная сезонность", "состояние настила после дождя"],
  "rationale": "Найдена в профильном каталоге и OSM, подходит под спокойную прогулку."
}
```

---

## 6. Deep research: целевое поведение

Настоящий deep research должен идти только через:

```txt
POST /api/ai/research-jobs
```

`searchMode: deep` в `/api/ai/search` сейчас нужно считать не deep research, а rerank. Его лучше переименовать в `rerank` или убрать из пользовательской логики.

Deep research должен делать не “больше генерации”, а больше проверки:

```txt
1. Официальные источники
2. Карты/координаты
3. Отзывы/репутация
4. Цена/часы/билеты
5. Маршрут/парковка/общественный транспорт
6. Противоречия/устаревшие страницы
```

Целевой deep pipeline:

```txt
create research job
→ plan branches
→ source search
→ open pages
→ extract structured facts
→ cross-check
→ reject weak candidates
→ final cards
→ final Russian memo
```

Branch-запросы:

```txt
main:      базовый запрос
official:  официальный сайт часы цена адрес
reviews:   отзывы актуально плюсы минусы
route:     как добраться парковка координаты маршрут
nearby:    рядом интересные места кафе прогулка
staleness: дата обновления, закрыто, ремонт, сезонность
```

---

## 7. Патч: `applyCardAdvice`

Проблема: модель выбирает лучшие карточки, а код добавляет невыбранные обратно.

Нужно заменить логику на такую:

```ts
private applyCardAdvice(cards: AiSearchCard[], adviceText: string) {
  const parsed = extractJsonObject(adviceText);
  if (!parsed?.cards?.length) return cards;

  const byTitle = new Map(cards.map((card) => [normalizeTitle(card.title), card]));
  const used = new Set<string>();

  const advised = parsed.cards.flatMap((advice) => {
    const title = compact(advice.title, '');
    const card = byTitle.get(normalizeTitle(title));
    if (!card || used.has(normalizeTitle(card.title))) return [];
    used.add(normalizeTitle(card.title));

    return [{
      ...card,
      rationale: compact(advice.rationale, card.rationale),
      notes: compact(advice.notes, card.notes),
      verification: advice.verification ?? card.verification,
    }];
  });

  return advised.length ? advised : cards;
}
```

Тест:

```txt
модель выбрала 2 карточки из 8 → наружу ушли только эти 2
```

---

## 8. Патч: CRW/SearXNG

`searchCrw()` должен стать не card generator, а candidate/source generator.

Новая логика:

```ts
private async searchCrw(
  input: AgentSearchInput,
  context: SearchContext,
): Promise<{ cards: AiSearchCard[]; sources: ResearchSource[] }> {
  if (!this.options.searchServiceBaseUrl) return { cards: [], sources: [] };

  const payload = await fetchCrw(...);

  const results = normalizeCrwResults(payload)
    .filter(regionRelevant)
    .filter(notKnownSpam)
    .filter(hasUsableUrl);

  return {
    cards: [],
    sources: results.map(toResearchSource),
  };
}
```

Тесты:

```txt
CRW вернул reddit/junodownload/мусор → cards.length === 0
CRW вернул официальный сайт парка → sources.length === 1, cards.length === 0
```

Карточка может появиться только после:

```txt
source.url opened
facts extracted
verification report built
```

---

## 9. Патч: KudaGo

KudaGo оставить, но понизить статус до источника кандидатов.

Правила:

```txt
KudaGo для events:
  - может дать candidate
  - должен фильтроваться по дате
  - должен иметь place/address
  - должен иметь source url
  - без opened page всегда needs_check
  - для nature/food не должен доминировать
```

Добавить проверку даты:

```ts
const isOnRequestedDate = (item: KudaGoSearchItem, date?: string) => {
  if (!date) return true;
  if (!item.dates?.length) return false;

  const target = new Date(`${date}T12:00:00.000Z`).getTime() / 1000;

  return item.dates.some((range) => {
    const start = range.start ?? 0;
    const end = range.end ?? range.start ?? 0;
    return start <= target && target <= end;
  });
};
```

Использовать:

```ts
(payload.results ?? [])
  .filter((item) => isOnRequestedDate(item, input.date))
  .filter((item) => item.place?.title || item.place?.address)
```

Карточке ставить:

```ts
verification: 'needs_check',
rationale: 'Найдено в агрегаторе событий; дату, билеты и площадку надо сверить по источнику.'
```

---

## 10. Патч: eco-trails

Сейчас eco-trails парсит каталог и делает карточку из текста ссылки. Это лучше, чем SERP, но недостаточно.

Целевой pipeline:

```txt
catalog page
→ route links
→ each route page opened
→ extract length/difficulty/start/seasonality/access/rules
→ final nature card
```

Добавить отдельный source toggle:

```ts
export interface AgentSourceSettings {
  twoGis: boolean;
  crw: boolean;
  kudago: boolean;
  osm: boolean;
  ecoTrails: boolean;
  codex: boolean;
}
```

В UI добавить:

```txt
Eco-trails: включен / недоступен / ошибка каталога / последняя проверка
```

В TypeScript-части отвязать ecoTrails от `crw`:

```ts
sourceSettings.ecoTrails ? this.searchEcoTrails(input, context) : Promise.resolve({ cards: [], sources: [] })
```

---

## 11. Crawl4AI и Scrapling

Crawl4AI уже есть в compose и sidecar. Его оставить основным page opener’ом.

Нужно довести wrapper:

```txt
- pin image version, не latest
- healthcheck
- auth token required
- timeout per page
- max pages per job
- max content length
- finalUrl capture
- failure reason capture
- per-domain rate limit
- block private IP / localhost SSRF
- cache by URL + content hash
```

Scrapling добавлять позже точечно, не как главный фикс:

```txt
- eco-trails detail pages, если HTML плавает
- афиша/площадки, если JS мешает
- страницы парков, если нужен устойчивый site-specific extractor
```

Главный недостающий кусок сейчас — не ещё один краулер, а evidence gate.

---

## 12. Sidecar как главный мозг deep research

Sidecar должен стать главным evidence pipeline.

Добавить в `research-sidecar/app.py`:

```py
@dataclass
class ExtractedFact:
    field: str
    value: str
    source_url: str
    source_name: str
    trust_tier: str
    confidence: str
    checked_at: str = field(default_factory=NOW)
```

Добавить extractors:

```py
def extract_address(text: str) -> list[ExtractedFact]
def extract_opening_hours(text: str) -> list[ExtractedFact]
def extract_price(text: str) -> list[ExtractedFact]
def extract_dates(text: str) -> list[ExtractedFact]
def extract_coordinates(text: str) -> list[ExtractedFact]
def extract_route_access(text: str) -> list[ExtractedFact]
def extract_reviews_signal(text: str) -> list[ExtractedFact]
def classify_trust_tier(url: str, source_name: str) -> str
```

Добавить verifier:

```py
def verify_candidate(candidate, facts, input_data, intent):
    ...
```

---

## 13. Verification logic

Не путать:

```txt
rankScore — насколько вариант подходит.
verificationStatus — насколько факты проверены.
```

Пример правил:

```py
def verification_status(candidate, facts):
    has_opened_source = any(f.source_url == candidate.url for f in facts)
    has_official = any(f.trust_tier == "official" for f in facts)
    has_map = any(f.trust_tier == "map" for f in facts)
    has_catalog = any(f.trust_tier == "catalog" for f in facts)

    existence_high = has_official or has_map or has_catalog
    two_independent_sources = len({f.source_url for f in facts}) >= 2

    if existence_high and (has_official or two_independent_sources):
        return "verified"

    if existence_high:
        return "partially_verified"

    if has_opened_source:
        return "needs_check"

    return "rejected"
```

Для UI нужны 4 статуса:

```txt
verified — можно почти отправлять, но всё равно открыть источник перед выходом
partially_verified — место существует, но цена/часы/маршрут не добиты
needs_check — идея интересная, нужна ручная проверка
rejected — не показывать в обычных результатах, только в research report
```

---

## 14. Trust tiers

Централизованный классификатор:

```txt
official:
  - официальный сайт парка/музея/ресторана/площадки
  - gov/spb/lo/park domains
  - домен самого места

map:
  - 2GIS
  - OpenStreetMap
  - Nominatim/Overpass-derived object

catalog:
  - eco-trails
  - профильные каталоги маршрутов

aggregator:
  - KudaGo
  - афиши
  - подборки событий

review:
  - отзывы, блоги, соцсети, подборки

search:
  - CRW/SearXNG snippets
```

Правило:

```txt
search trust tier не может делать verified.
aggregator один сам по себе не может делать verified.
official/map/catalog могут повышать confidence.
```

---

## 15. Ранжирование

Сделать score объяснимым.

```py
score = 0

# intent match
+30 если type совпадает с intent
-50 если type конфликтует

# trust
+40 official
+35 map
+30 catalog
+15 aggregator
+5 review
+0 search

# evidence
+15 opened source
+15 address found
+10 hours found
+10 price found
+15 date matches requested date
+10 route/access found
+10 coordinates found

# couple fit
+20 low/medium energy if requested calm
+15 within radius
+10 good weather compatibility
+10 matches saved preferences

# penalties
-100 spam/source blacklist
-80 wrong city/region
-60 no usable URL
-50 snippet only
-40 stale date
-30 missing address for food/event
-20 too far
```

---

## 16. Hard reject rules

Вынести в один файл:

```txt
calendar-nanobot/src/sourcePolicy.ts
research-sidecar/source_policy.py
```

Правила:

```txt
- wrong region
- wrong intent
- no URL
- SERP snippet only
- casino/adult/gambling/medicine/random ecommerce
- music download sites
- Reddit/social noise, если не review branch
- title with mojibake/encoding garbage
- “карта”, “условные обозначения”, “легенда” как place title
- bank/ATM/offices for food queries
- event without date when date requested
- food without address/map evidence
- nature route without start/region/source
```

---

## 17. Agent modes: нормальное значение режимов

Оставить режимы:

```txt
auto
fast_xcody
deep_xcody
codex_subscription
```

Переопределить смысл:

```txt
auto:
  deterministic tools + sidecar where available + cheap rerank

fast_xcody:
  quick search + model rerank existing cards only

deep_xcody:
  deep research job + sidecar + model synthesis over evidence

codex_subscription:
  verifier/synthesis, не primary source of truth
```

Модель не должна иметь права создавать новые факты.

---

## 18. Prompt contract для rerank

Системный контракт:

```txt
You receive existing activity cards only.

You may:
- keep cards
- reorder cards
- mark caveats
- lower verification
- reject weak cards

You must not:
- create new cards
- create URLs
- create addresses
- create prices
- create opening hours
- upgrade verification without evidence
```

Ответ только JSON:

```json
{
  "cards": [
    {
      "title": "exact existing title",
      "decision": "keep",
      "rationale": "почему подходит",
      "notes": "что проверить руками",
      "verification": "verified|partially_verified|needs_check",
      "confidence": "low|medium|high"
    }
  ],
  "rejected": [
    {
      "title": "exact existing title",
      "reason": "why rejected"
    }
  ]
}
```

Код обязан реально выкидывать `rejected`.

---

## 19. Prompt contract для deep synthesis

Финальный deep agent должен возвращать не только memo, а machine-readable decision.

```json
{
  "summary": "короткий русский итог",
  "cards": [
    {
      "sourceTitle": "exact existing title",
      "action": "keep",
      "correctedFields": {
        "notes": "...",
        "rationale": "...",
        "travel": "...",
        "price": "..."
      },
      "verification": "partially_verified",
      "missingFacts": ["часы", "цена"]
    }
  ],
  "rejected": [
    {
      "sourceTitle": "...",
      "reason": "нет проверяемого адреса"
    }
  ],
  "manualChecks": [
    "перед поездкой открыть официальный сайт"
  ]
}
```

---

## 20. UI: карточка идеи

На карточке показать:

```txt
- badge: Проверено / Частично проверено / Нужно проверить
- checkedAt
- источник
- что проверено
- что не проверено
- why this fits us
- distance confidence
- price confidence
- hours confidence
```

Пример:

```txt
Комаровский берег
Частично проверено · eco-trails + OSM · проверено 28.06.2026

Почему нам:
спокойная прогулка, не слишком далеко, подходит для фотоотчёта.

Проверено:
маршрут существует, район подходит, примерная длина есть.

Проверить перед поездкой:
состояние настила после дождя, точку старта, ограничения.
```

---

## 21. UI: deep research job

Показывать progress events:

```txt
Планирую подзапросы
Ищу официальные источники
Открываю страницы
Извлекаю факты
Отбрасываю мусор
Собираю карточки
```

Показывать counts:

```txt
candidates found: 42
pages opened: 16
facts extracted: 73
rejected: 31
final cards: 5
```

---

## 22. UI: админка агента

Добавить статусы:

```txt
Nanobot: ok/down
Sidecar: ok/down
Crawl4AI: ok/down
CRW: ok/down
SearXNG: ok/down
2GIS: key ok/missing
KudaGo: reachable/unreachable
OSM/Nominatim: reachable/rate-limited
Overpass: reachable/rate-limited
Codex: installed/logged in/enabled
Mode: normal/degraded/fallback
```

Добавить тесты в админке:

```txt
Тест “экотропа”
Тест “кофе”
Тест “выставка”
```

Не один тест `query: кофе`.

---

## 23. API changes

### `/api/ai/search`

Возвращать:

```ts
{
  provider: string;
  mode: 'quick';
  degraded: boolean;
  cards: AiSearchCard[];
  sources: ResearchSource[];
  warnings: string[];
}
```

### `/api/ai/research-jobs`

Сделать единственным настоящим deep path.

Сохранять в run:

```ts
{
  query,
  city,
  radiusKm,
  date,
  kind,
  intent,
  sourceSettingsSnapshot,
  providerSnapshot,
  degraded,
}
```

### `/api/admin/agent-settings`

Добавить:

```ts
sidecar: {
  configured: boolean;
  reachable: boolean;
  indexReady: boolean;
  vectorReady: boolean;
}

crawl4ai: {
  configured: boolean;
  reachable: boolean;
  version?: string;
}
```

---

## 24. Database/index

Sidecar уже создаёт:

```txt
research_documents
research_chunks
research_candidates
```

Добавить:

```sql
create table if not exists research_evidence (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid,
  url text not null,
  field text not null,
  value text not null,
  source_name text not null default '',
  trust_tier text not null default 'web',
  confidence text not null default 'low',
  checked_at timestamptz not null default now()
);

create table if not exists research_rejections (
  id uuid primary key default gen_random_uuid(),
  run_id text not null,
  title text not null,
  url text not null default '',
  source_name text not null default '',
  reason text not null,
  checked_at timestamptz not null default now()
);
```

Кандидаты должны хранить:

```txt
normalized_key
canonical_url
first_seen_at
last_checked_at
last_good_at
last_status
rank_score
verification_status
facts jsonb
missing_facts jsonb
```

---

## 25. Кэш и свежесть

Правила freshness:

```txt
events:
  cache 1–6 часов
  обязательно проверять дату/билеты ближе к визиту

restaurants:
  cache 1–7 дней
  часы/средний чек могут устареть

eco trails:
  cache 7–30 дней
  сезонность/ремонты/закрытия проверять перед поездкой

weather:
  cache по date/location
  ближе к дате обновлять чаще

SERP:
  cache короткий, 1–24 часа
```

В карточке показывать:

```txt
Проверено: 28.06.2026 14:20
Источник: official/catalog/map
Свежесть: норм / устарело / проверить
```

---

## 26. Гео и дорога

Сейчас расчёт дороги — грубый haversine × коэффициент. Это нормально как fallback, но не как “маршрут”.

Нужно:

```txt
- использовать home_address → geocode → home_point
- хранить координаты дома как preference, а не каждый раз геокодировать
- для кандидатов доставать координаты из 2GIS/OSM/страниц
- distanceConfidence:
    high: есть координаты дома и места
    medium: есть координаты места, дом fallback
    low: нет координат места
```

Позже можно добавить OSRM/GraphHopper/Яндекс/2GIS routing, но сначала достаточно честного confidence.

---

## 27. Погода

Open-Meteo оставить.

Добавить weather relevance by type:

```txt
nature: важна
food: почти не важна
exhibition/concert: не критично
```

Добавить weather risk:

```txt
rain
snow
wind
cold
heat
```

Card warning:

```txt
“лучше сухая погода”
“запасной indoor-вариант”
“после дождя может быть грязно”
```

---

## 28. Фотоотчёты и память пары

Использовать visits/photos как память пары.

После посещения:

```txt
- карточка становится visit
- фото прикрепляются к visit
- rating/notes сохраняются
- агент использует историю:
    “нам понравилось”
    “слишком далеко”
    “не любим шумные места”
    “лучше недорого”
    “после дождя тропы не хотим”
```

Добавить preferences extraction:

```txt
После rating/notes агент может предложить:
“Запомнить: избегать мест дальше 80 км?”
“Запомнить: любим спокойные тропы 3–7 км?”
```

Автозапоминание — только с подтверждением.

---

## 29. Privacy / relationship safety

Не делать:

```txt
- кто чаще отказывается
- кто виноват
- score отношений
- pressure streaks
- статистику отказов
```

Можно хранить:

```txt
- place feedback
- понравилось/не понравилось
- усталость/энергия
- “далеко/норм/близко”
- “шумно/тихо”
```

---

## 30. Observability

Добавить structured logs:

```json
{
  "runId": "...",
  "query": "...",
  "intent": "nature",
  "provider": "sidecar",
  "degraded": false,
  "sources": {
    "crw": 12,
    "ecoTrails": 8,
    "kudago": 0,
    "osm": 5,
    "2gis": 0
  },
  "openedPages": 14,
  "extractedFacts": 52,
  "rejected": 17,
  "finalCards": 5,
  "durationMs": 42000
}
```

Метрики:

```txt
- p50/p95 quick search time
- p50/p95 deep job time
- source error rate
- crawler success rate
- rejected reason counts
- fallback rate
- no-result rate
- cards per query
- verified/needs_check ratio
```

Админка должна показывать:

```txt
Последний deep research:
  candidates: 42
  pages opened: 16
  rejected: 31
  final: 5
  degraded: no
```

---

## 31. Security / safety

Соблюдать правило: не обходить CAPTCHA, login walls и anti-abuse controls.

Добавить в код:

```txt
- SSRF protection for crawler URLs
- block localhost/private IP ranges
- allow only http/https
- max redirects
- max response size
- max pages per job
- per-domain delay
- token required for sidecar/crawl4ai
- no secrets in logs
- no env dump in admin
```

---

## 32. Docker / deploy

В compose уже есть:

```txt
calendar-web
calendar-nanobot
calendar-research-sidecar
Postgres/pgvector
MinIO
SearXNG
CRW
crawl4ai
```

Доделать:

```yaml
crawl4ai:
  image: unclecode/crawl4ai:<pinned-version>
  shm_size: 1gb
  environment:
    CRAWL4AI_API_TOKEN: ${CRAWL4AI_API_TOKEN}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:11235/health"]
    interval: 30s
    timeout: 10s
    retries: 3

calendar-research-sidecar:
  depends_on:
    crawl4ai:
      condition: service_healthy
    crw:
      condition: service_started
```

Добавить healthchecks для:

```txt
calendar-nanobot
calendar-research-sidecar
crw
searxng
crawl4ai
postgres
```

---

## 33. Нормальный конфиг

```env
CALENDAR_AGENT_MODE=auto

CALENDAR_NANOBOT_BASE_URL=http://calendar-nanobot:4185
CALENDAR_NANOBOT_TOKEN=...

CALENDAR_RESEARCH_SIDECAR_BASE_URL=http://calendar-research-sidecar:8095
CALENDAR_RESEARCH_TOKEN=...

SEARCH_SERVICE_BASE_URL=http://crw:3000
SEARCH_SERVICE_TOKEN=...

CRAWL4AI_BASE_URL=http://crawl4ai:11235
CRAWL4AI_API_TOKEN=...

TWOGIS_API_KEY=...

CODEX_ENABLED=true
CODEX_EXEC_PATH=codex

NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
ECO_TRAILS_CATALOG_URL=https://eco-trails.ru/catalog/?region=lenoblast
```

`CODEX_ENABLED=true` только если реально:

```txt
codex installed
codex logged in
admin status says ready
```

Иначе не включать как основной режим.

---

## 34. Golden queries

Добавить набор эталонных запросов:

```txt
1. “экотропы рядом с СПб”
2. “спокойная экотропа без машины”
3. “уютный ужин вдвоём тихо”
4. “кофе и прогулка вечером”
5. “выставка в выходные СПб”
6. “камерный концерт завтра”
7. “место с красивыми фото до 80 км”
8. “куда съездить если дождь”
9. “прогулка без толпы”
10. “что-то недорогое на вечер”
```

Expected assertions:

```txt
- no CRW-only cards
- no wrong region
- no banks/offices for food
- no KudaGo dominance for nature/food
- event cards match requested date or are marked needs_check
- final cards <= 7
- every card has URL
- every card has checkedAt
- every card has verification
- every card has missingFacts
- rejectedCandidates is not empty when spam exists
```

---

## 35. Unit tests

```txt
providerRouter.applyCardAdvice:
  - rejected leftovers do not return

researchTools.searchCrw:
  - CRW returns sources only, no cards

researchTools.searchKudaGo:
  - event outside requested date rejected
  - event without dates becomes needs_check or rejected

researchTools.search:
  - nature query orders ecoTrails before KudaGo/CRW
  - food query does not include museums/banks/offices

sourceSettings:
  - ecoTrails can be enabled while crw disabled

sidecar.verify_candidate:
  - high score without evidence is not verified
  - official source upgrades confidence
  - search-only source cannot verify

sidecar.deadline:
  - max_runtime_seconds stops page opening

sidecar.search_kudago:
  - city mapping is not hardcoded to spb

routes.createResearchRun:
  - date is persisted

admin status:
  - shows sidecar/crawl4ai degraded state
```

---

## 36. Integration tests

Mock services:

```txt
fake CRW
fake KudaGo
fake 2GIS
fake OSM
fake Crawl4AI
fake eco-trails
```

Scenarios:

```txt
CRW returns 10 spam results:
  result cards = 0 or clean fallback
  rejectedCandidates contains spam reasons

KudaGo returns event without requested date:
  event rejected or needs_check

eco-trails catalog returns route:
  sidecar opens detail page
  extracts length/difficulty
  final card has nature type

2GIS returns bank for food query:
  rejected

Crawl4AI down:
  direct HTTP fallback works
  job degraded warning shown

Sidecar down:
  nanobot falls back
  UI says degraded
```

---

## 37. Acceptance criteria для “идеально”

Считать готовым, когда:

```txt
1. По “экотропы рядом с СПб” нет KudaGo-спама.
2. По “ужин вдвоём” нет банков, музеев, офисов, школ.
3. По “выставка в выходные” события не вне даты.
4. CRW/SearXNG сниппеты не попадают в финальные карточки.
5. Deep research открывает страницы и показывает rejected candidates.
6. verified не ставится без opened evidence.
7. UI явно показывает, что надо проверить руками.
8. fallback не маскируется под нормальный поиск.
9. sidecar/crawl4ai/crw статусы видны в админке.
10. У каждого результата есть source, checkedAt, verification, missingFacts.
11. Агент не придумывает URL/адрес/цену/часы.
12. Если нормальных вариантов нет — система честно говорит “не нашёл”, а не выдумывает.
```

---

## 38. Самый короткий список максимального эффекта

```txt
- Починить applyCardAdvice: не возвращать rejected leftovers.
- Запретить searchCrw создавать AiSearchCard.
- Настоящий deep research вести только через /api/ai/research-jobs.
- Разделить score и verification.
- Добавить evidence facts.
- Фильтровать KudaGo по date.
- Добавить ecoTrails source toggle.
- Показать degraded/fallback mode в UI.
- Добавить sidecar/crawl4ai health в админку.
- Расширить тесты на spam/reject/verified.
```

---

## 39. Codex/Cursor/agent prompt для выполнения этого плана

Можно скормить агенту как задачу:

```txt
You are working in the couple-calendar repo.
Implement the evidence-based research refactor described in couple_calendar_research_monster_plan.md.

Hard constraints:
- Do not rewrite the whole app.
- Preserve Browser → Express → calendar-nanobot → typed tools/sidecar architecture.
- CRW/SearXNG must not create final AiSearchCard directly.
- KudaGo must be treated as event candidate source, not verified truth.
- applyCardAdvice must not re-add rejected cards.
- Deep research must use /api/ai/research-jobs and sidecar path.
- Verification must be evidence-based, not score-based.
- Add tests for each behavior changed.
- Keep privacy boundaries: no relationship scoring, no refusal stats.
- Do not bypass CAPTCHA/login/anti-abuse controls.

Start by making the smallest safe changes with tests:
1. Fix applyCardAdvice leftovers.
2. Make CRW return sources only.
3. Add KudaGo date filtering.
4. Add ecoTrails source toggle.
5. Split rankScore and verificationStatus in sidecar.
6. Add degraded/fallback warnings.
7. Add admin health statuses.
```

---

## 40. Финальная мысль

Сейчас система выглядит как “агент плохо ресерчит”, но реальная проблема ниже:

```txt
Сырые источники слишком рано считаются карточками.
Модель ранжирует мусор вместо проверки evidence.
Fallback маскируется под нормальный режим.
Verification зависит от score, а не от фактов.
```

После исправления контракта pipeline модели станут выглядеть намного умнее, потому что им останется нормальная работа: выбрать из проверенных вариантов, объяснить компромиссы, собрать план дня и честно подсветить риски.
