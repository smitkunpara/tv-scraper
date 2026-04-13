# News

!!! info "Version Note"
    `get_news()` uses the News Flow v2 API and was added in `1.4.0b1`.

`News` gives you three separate entry points:

- `get_news()` for flow-style filtered news
- `get_news_headlines()` for symbol headlines
- `get_news_content()` for full article content

## Methods

### `get_news(...)`

```python
from tv_scraper import News

scraper = News()
result = scraper.get_news(
    symbol="NASDAQ:AAPL",
    provider=["reuters"],
    market_country=["US"],
    market=["stock"],
    language="en",
    limit=10,
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "id": "tag:provider.com,2026:newsml_123:0",
            "title": "Headline title",
            "published": 1700000000,
            "urgency": 2,
            "permission": "free",
            "relatedSymbols": [{"symbol": "NASDAQ:AAPL"}],
            "storyPath": "/news/path",
            "provider": {"id": "reuters", "name": "Reuters", "logo_id": "reuters_logo"},
            "is_flash": False,
        },
        ...,
    ],
    "metadata": {...},
    "error": None,
}
```

### `get_news_headlines(...)`

```python
result = scraper.get_news_headlines(
    exchange="NASDAQ",
    symbol="AAPL",
    provider="reuters",
    area="americas",
    sort_by="latest",
    section="all",
    language="en",
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "id": "tag:provider.com,2026:newsml_123:0",
            "title": "Headline title",
            "shortDescription": "Short summary",
            "published": 1700000000,
            "storyPath": "/news/path",
        },
        ...,
    ],
    "metadata": {...},
    "error": None,
}
```

### `get_news_content(...)`

```python
content = scraper.get_news_content(
    story_id="tag:reuters.com,2026:newsml_example:0",
    language="en",
)
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "id": "tag:provider.com,2026:newsml_123:0",
        "title": "Headline title",
        "description": "Merged article text",
        "published": 1700000000,
        "storyPath": "/news/path",
    },
    "metadata": {...},
    "error": None,
}
```

## Accepted Inputs

### `get_news(...)`

- `symbol`: optional full symbol such as `NASDAQ:AAPL`
- `provider`: [News providers](../supported_data.md#news-providers)
- `market_country`: [News countries](../supported_data.md#news-countries)
- `sector`: [News sectors](../supported_data.md#news-sectors)
- `corp_activity`: [News corporate activities](../supported_data.md#news-corporate-activities)
- `economic_category`: [News economic categories](../supported_data.md#news-economic-categories)
- `market`: [News asset markets](../supported_data.md#news-asset-markets)
- `language`: [Languages](../supported_data.md#languages)

### `get_news_headlines(...)`

- `exchange`: [Exchanges](../supported_data.md#exchanges)
- `provider`: [News providers](../supported_data.md#news-providers)
- `area`: [News areas](../supported_data.md#news-areas)
- `sort_by`: `latest`, `oldest`, `most_urgent`, `least_urgent`
- `section`: `all`, `esg`, `press_release`, `financial_statement`
- `language`: [Languages](../supported_data.md#languages)

### `get_news_content(...)`

- `story_id`: non-empty story id string
- `language`: [Languages](../supported_data.md#languages)

!!! failure "wrong input"
    This is wrong for `area` because the input value should be the readable key, not the mapped code.

    ```python
    scraper.get_news_headlines(
        exchange="NASDAQ",
        symbol="AAPL",
        area="WLD",
    )
    ```

    Use:

    ```python
    scraper.get_news_headlines(
        exchange="NASDAQ",
        symbol="AAPL",
        area="world",
    )
    ```

!!! note "Notes"
    - `get_news()` applies `limit` client-side after the fetch.
    - `get_news()` rejects filter combinations that would create a URL longer than 4096 characters.
    - `get_news_content()` requires a non-empty `story_id`.
