# News Scraper

## Overview

`News` scrapes TradingView headlines and full story content.

- Headlines endpoint: `https://news-headlines.tradingview.com/v2/view/headlines/symbol`
- Story endpoint: `https://news-mediator.tradingview.com/public/news/v1/story`

## Constructor

```python
from tv_scraper.scrapers.social import News

scraper = News(
    export_result=False,
    export_type="json",
    timeout=10,
    cookie=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export headlines result to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `timeout` | `int` | `10` | HTTP timeout in seconds |
| `cookie` | `str \| None` | `None` | TradingView cookie. If omitted, `TRADINGVIEW_COOKIE` env var is used when available |

## Method: `get_news_headlines()`

```python
def get_news_headlines(
    exchange: EXCHANGE_LITERAL,
    symbol: str,
    provider: NEWS_PROVIDER_LITERAL | None = None,
    area: AREA_LITERAL | None = None,
    sort_by: Literal["latest", "oldest", "most_urgent", "least_urgent"] = "latest",
    section: Literal["all", "esg", "press_release", "financial_statement"] = "all",
    language: str = "en",
) -> dict[str, Any]
```

### Validation

- `exchange` + `symbol` are verified with a live TradingView symbol check.
- `sort_by` must be one of: `latest`, `oldest`, `most_urgent`, `least_urgent`.
- `section` must be one of: `all`, `esg`, `press_release`, `financial_statement`.
- `provider` (if set) must exactly match one of:
  - `the_block`, `cointelegraph`, `beincrypto`, `newsbtc`, `dow-jones`, `cryptonews`, `coindesk`, `cryptoglobe`, `tradingview`, `zycrypto`, `todayq`, `cryptopotato`, `u_today`, `cryptobriefing`, `coindar`, `bitcoin_com`
- `area` (if set) validates against area names and codes:
  - names: `world`, `americas`, `europe`, `asia`, `oceania`, `africa`
  - codes: `WLD`, `AME`, `EUR`, `ASI`, `OCN`, `AFR`
- `language` must be one of:
  - `en`, `de`, `fr`, `es`, `it`, `pt`, `ru`, `ja`, `ko`, `ar`, `hi`, `sv`, `tr`, `th`, `vi`, `id`, `fa`, `ch`, `ms`, `el`, `he`

### Request and Filtering Behavior

- API request params include `symbol="{exchange}:{symbol}"`, `client="web"`, and `streaming=""`.
- `section="all"` is sent as an empty `section` value.
- `provider` is sent as `provider.replace(".", "_")`.
- `area` is sent as `AREAS.get(area, "")`.
  - This means area names map to TradingView area codes.
  - Passing a raw area code validates, but currently sends an empty area filter.
- Sorting is applied client-side after fetch:
  - `latest` / `oldest` sort by `published`
  - `most_urgent` / `least_urgent` sort by `urgency`

### Headline Output Items

Each `data` item contains:

```json
{
  "id": "tag:provider.com,2026:newsml_123:0",
  "title": "Headline title",
  "shortDescription": "Short summary",
  "published": 1700000000,
  "storyPath": "/news/path"
}
```

Notes:

- `storyPath` is normalized to always start with `/` when non-empty.
- If `items` is missing or empty, returns success with `data=[]` and `metadata.total=0`.
- Export is only triggered by `get_news_headlines()` when `export_result=True`.

## Method: `get_news_content()`

```python
def get_news_content(
    story_id: str,
    language: str = "en",
) -> dict[str, Any]
```

### Validation

- `story_id` must not be empty or whitespace-only.
- `language` uses the same language validation as headlines.

### Behavior

- Sends request params: `id`, `lang`, `user_prostatus="non_pro"`.
- Parses output into:
  - `id`, `title`, `published`, `storyPath`, `description`
- `description` is built from `ast_description.children`:
  - only top-level paragraph nodes (`type == "p"`) are used
  - paragraph text merges raw strings and object `params.text` values
  - paragraphs are joined with newline characters

## Response Envelope (Both Methods)

Both methods return the standard envelope:

```json
{
  "status": "success",
  "data": {},
  "metadata": {},
  "error": null
}
```

Failure shape:

```json
{
  "status": "failed",
  "data": null,
  "metadata": {},
  "error": "error message"
}
```

Metadata behavior:

- Metadata is auto-captured from method arguments.
- Arguments passed as `None` are omitted from metadata.
- `get_news_headlines()` adds `metadata.total` on success.

## Usage Examples

### Headlines

```python
from tv_scraper.scrapers.social import News

scraper = News()
result = scraper.get_news_headlines(
    exchange="NASDAQ",
    symbol="AAPL",
    sort_by="latest",
    section="all",
    language="en",
)
```

### Story Content

```python
headlines = scraper.get_news_headlines(exchange="NASDAQ", symbol="AAPL")

if headlines["status"] == "success" and headlines["data"]:
    story_id = headlines["data"][0]["id"]
    content = scraper.get_news_content(story_id=story_id, language="en")
```

### Validation Error Example

```python
result = scraper.get_news_content(story_id="   ")
# result["status"] == "failed"
# result["error"] == "story_id cannot be empty"
```
