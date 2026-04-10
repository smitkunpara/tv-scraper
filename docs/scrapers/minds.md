# Minds Scraper

## Overview

`Minds` fetches community discussions from TradingView Minds with cursor pagination.
Requests are made to `https://www.tradingview.com/api/v1/minds/`.

All public responses use the standard envelope:

- `status`: `success` or `failed`
- `data`: parsed list on success, `None` on failure
- `metadata`: call metadata and scraper metadata
- `error`: `None` on success, message on failure

## API

### Constructor

```python
from tv_scraper.scrapers.social import Minds

scraper = Minds(
	export_result=False,
	export_type='json',
	timeout=10,
	cookie=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export data to file when `True` |
| `export_type` | `str` | `json` | Export format: `json` or `csv` |
| `timeout` | `int` | `10` | HTTP timeout in seconds |
| `cookie` | `str \| None` | `None` | Optional TradingView session cookie; falls back to `TRADINGVIEW_COOKIE` env var |

### get_minds

```python
result = scraper.get_minds(exchange='NASDAQ', symbol='AAPL', limit=50)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `EXCHANGE_LITERAL` | - | Exchange name, validated with `symbol` |
| `symbol` | `str` | - | Trading symbol |
| `limit` | `int \| None` | `None` | Optional final output cap |

`limit` behavior exactly as implemented:

- If `limit is None`, no truncation is applied.
- If `limit` is provided and `len(parsed_data) > limit`, the final list is sliced with `parsed_data[:limit]`.
- Truncation happens after pagination finishes.
- `limit` is included in `metadata` only when it is not `None`.

## Cursor Pagination

Pagination flow in `get_minds`:

1. Build `combined_symbol = f'{exchange}:{symbol}'`.
2. Request first page with params `{'symbol': combined_symbol}`.
3. If a cursor exists, request next pages with param `c`.
4. Read cursor from `next` only if `'?c='` exists.
5. Cursor extraction uses the first value after `'?c='` up to `&`.

The loop stops when:

- `results` is empty
- `next` is empty
- `next` does not contain `'?c='`
- cursor value after `'?c='` is empty
- `pages >= MAX_PAGES` before a new request

## MAX_PAGES Safeguard

`MAX_PAGES = 100`.

When the cap is reached, the scraper logs a warning and stops fetching more pages. It still returns a success response with the data collected so far.

## Parsed Output Schema

Each result item is normalized by `_parse_mind` to:

| Field | Type | Source / behavior |
|-------|------|-------------------|
| `text` | `str` | `item.get('text', '')` |
| `url` | `str` | `item.get('url', '')` (kept as-is, often relative) |
| `author.username` | `str \| None` | `author.get('username')` |
| `author.profile_url` | `str` | `author.get('uri', '')`; prefixed with `https://www.tradingview.com` when URI does not start with `http` |
| `author.is_broker` | `bool` | `author.get('is_broker', False)` |
| `created` | `str` | Parsed and formatted, or original value on parse failure |
| `total_likes` | `int` | `item.get('total_likes', 0)` |
| `total_comments` | `int` | `item.get('total_comments', 0)` |

### Timestamp Formatting

Formatting logic is:

```python
created_datetime = datetime.fromisoformat(created.replace('Z', '+00:00'))
created_formatted = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
```

If parsing raises `ValueError` or `AttributeError`, `created` is returned unchanged.

## Response Envelope

Success response shape:

```python
{
	'status': 'success',
	'data': [
		{
			'text': 'Test mind',
			'url': '/mind/1',
			'author': {
				'username': 'user',
				'profile_url': 'https://www.tradingview.com/u/user',
				'is_broker': False,
			},
			'created': '2024-01-01 00:00:00',
			'total_likes': 5,
			'total_comments': 2,
		}
	],
	'metadata': {
		'exchange': 'NASDAQ',
		'symbol': 'AAPL',
		'limit': 50,
		'total': 1,
		'pages': 1,
		'symbol_info': {},
	},
	'error': None,
}
```

Metadata details:

- `@catch_errors` captures function args into metadata (`exchange`, `symbol`, and `limit` when not `None`).
- `get_minds` adds `total`, `pages`, and `symbol_info` on success.
- `symbol_info` is read from `meta.symbols_info[combined_symbol]` on the first page, or from the first empty page response when no rows are returned.

## Failure Behavior

`get_minds` returns failed envelopes (does not raise) for:

- validation errors from `validators.verify_symbol_exchange`
- request errors returned by `_request` (network, captcha, HTTP, parse)
- unexpected runtime exceptions (wrapped by `@catch_errors` with prefix `Unexpected error:`)

Failure response shape:

```python
{
	'status': 'failed',
	'data': None,
	'metadata': {
		'exchange': 'NASDAQ',
		'symbol': 'AAPL',
	},
	'error': 'Network error: ...',
}
```

If a request failure happens after some pages were already fetched, the method returns `data=None` and does not include partial rows in the failed response.

## Examples

```python
from tv_scraper.scrapers.social import Minds

scraper = Minds()
result = scraper.get_minds(exchange='NYSE', symbol='BRK.B', limit=10)

if result['status'] == 'success':
	print(result['metadata']['total'])
```
