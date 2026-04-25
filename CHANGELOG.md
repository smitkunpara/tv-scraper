# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.3] - 2026-04-25

### Added
- **Tests**: Added a unit test to verify `CandleStreamer`, `ForecastStreamer`, and `Streamer` are importable from the top-level package (`from tv_scraper import ...`).

### Changed
- **Documentation**: Standardized streaming examples to use top-level imports from `tv_scraper` instead of subpackage imports.

### Fixed
- **Streaming Imports**: Exported `CandleStreamer` and `ForecastStreamer` in `tv_scraper.__init__` so users no longer need deep module paths for streamer imports.

## [1.4.2] - 2026-04-22

### Fixed
- **Screener**: Fixed a validation bug where the `in_day_range` operation was incorrectly blocked. This allows filtering by earnings dates (e.g., today, yesterday, tomorrow).
- **Version Consistency**: Synchronized `tv_scraper.__version__` with package metadata.

### Added
- **Screener Operations**: Added support for a comprehensive list of TradingView scanner operations:
    - Day/Week/Month/Year ranges: `in_day_range`, `not_in_day_range`, `in_week_range`, `in_month_range`, `in_year_range`.
    - Text Matching: `match`, `nmatch`, `smatch`.
    - Empty Checks: `empty`, `nempty`.
    - Percentage Comparisons: `above%`, `below%`, `in_range%`.

## [1.4.1] - 2026-04-17

### Breaking Changes
- **Standardized Response Envelope**: Refactored `BaseScraper._success_response` and `_error_response` to include a top-level `warnings` field (dictionary key: `"warnings"`). This field is now always present in both success and error responses, defaulting to an empty list `[]`.

### Added
- **Standardized Warnings**: Added a top-level `warnings` field to the response envelope to communicate non-blocking issues, deprecations, or partial data status across all scrapers.

### Changed
- **Pine Scraper**: Refactored `validate_script`, `create_script`, and `edit_script` to utilize the new top-level `warnings` field for validation compiler warnings.
- **Streamer**: Added runtime deprecation warnings to the response envelopes of `get_candles()`, `get_forecast()`, and `get_available_indicators()`.
- **News Scraper**: Added a deprecation warning to the legacy `get_news_headlines()` method in the response envelope.
- **Documentation**: Standardized all project documentation (20+ files) across `docs/` to reflect the new response envelope structure, including updated JSON snapshots and field descriptions.


## [1.4.0] - 2026-04-16


### Breaking Changes
- **Core Validation**: Decentralized the validation architecture. Removed `tv_scraper.core.validators.py`. Validation is now integrated directly into the `BaseScraper` class and specific scraper subclasses.
- **Scraper API**: Strictly enforced the use of separate `exchange` and `symbol` parameters across all symbol-specific scrapers.
- **Scraper API**: Removed legacy support for combined `EXCHANGE:SYMBOL` strings in `News.get_news()` and `SymbolMarkets.get_symbol_markets()`. These methods now require both arguments explicitly.

### Added
- **Development Standards**: Updated `AGENTS.md` and contributing guidelines to mandate comprehensive edge-case testing for all new features and scraper methods.

### Changed
- **Scraper API**: Merged `export_result` and `export_type` constructor arguments into a single `export` parameter across all scrapers and streamers. Providing `"json"` or `"csv"` now automatically enables export in that format, while `None` (default) keeps it disabled.
- **Improved Encapsulation**: Scraper-specific validation logic (e.g., technical indicator and options verification) is now encapsulated within their respective classes (`Technicals`, `Options`).

### Fixed
- **Test Suite Stability**: Systematically refactored the entire test suite (1000+ tests) to align with decentralized validation and generic error message formatting (`Invalid value: '...'`).
- **Standardized Error Messages**: Unified validation error reporting across all scrapers, ensuring consistent error envelopes via the `@catch_errors` decorator.
- **Streaming**: `CandleStreamer` now validates custom Pine indicators before creating studies by using Pine tools (`get_script` + `validate_script`).
- **Tests**: Systematically updated all unit, mock, and live tests for `SymbolMarkets` and `News` to comply with the new mandatory `(exchange, symbol)` API.
- **Cleanup**: Removed obsolete migration and refactor scripts from the repository root.

## [1.4.0b2] - 2026-04-13

### Added
- **Streaming**: Added `stream_realtime_price()` and `get_available_indicators()` to `CandleStreamer` for better feature isolation.
- **Core Validation**: Added `validate_yyyymmdd_date(field_name, value)` to validate `YYYYMMDD` dates with month/day bounds and real calendar-date checks.
- **Test Suite**: Added `tests/unit/test_validators.py` to cover date validation rules and failure cases.

### Changed
- **Streaming**: Consolidated `stream_handler.py` into `base_streamer.py`, reducing the number of internal files.
- **Streaming**: `StreamHandler` is now imported from `tv_scraper.streaming.base_streamer`.
- **Options Scraper**: Unified options lookup into `get_options(exchange, symbol, expiration=None, strike=None, columns=None)`.
- **Options Scraper**: `get_options()` now supports combined filtering (`expiration` + `strike`) and uses standardized `filter_value` metadata for single and combined filters.
- **Options Scraper**: Added IDE-friendly `OPTION_COLUMN_LITERAL` typing for `columns` and kept runtime column validation against allowed option fields.
- **Options Scraper**: `expiration` now uses centralized validator checks (`0 < MM <= 12`, `0 < DD <= 31`, plus calendar validity).
- **Documentation**: Updated options and architecture docs to reflect the unified options API, strict date validation behavior, and column literal guidance.
- **Tests**: Updated options unit/mock/integration/live tests to use `get_options()` and added combined-filter coverage.
- **Technicals API**: Simplified `get_technicals()` by removing `all_indicators` and `fields`; `technical_indicators=None` now fetches the full indicator set.
- **Typing**: Added `INDICATOR_LITERAL` typing support and updated technicals tests/docs to match the new API behavior.
- **Docs**: Standardized method sections to "code first, output immediately below" and aligned streaming examples with fixture-backed structures.
- **Docs Versioning**: Added `mkdocs_hooks.py` and hooked it in `mkdocs.yml` to generate `versions.json` during local builds/serve for version-switcher compatibility.
- **CI/CD**: Updated `.github/workflows/gh-pages.yml` to support tag-triggered version deploys and conditional `mike set-default` behavior.

### Deprecated
- **Streaming**: The `Streamer` class in `tv_scraper.streaming.streamer` is now deprecated. It has been moved to a multi-streamer architecture for easier maintenance.

### Removed
- **Legacy Streaming Docs**: Removed `docs/streaming/base_streamer.md` from documentation flow.
- **Scripts**: Removed obsolete `scripts/verify_news.py` helper script.
- **Legacy Tests**: Removed archived `tests_backup` suite.


## [1.4.0b1] - 2026-04-11

### Added
- **Core**: New `http.py` module implementing a centralized `requests.Session` with automatic retry logic (exponential backoff) for improved network reliability.
- **News Scraper**: Integrated TradingView **News Flow (v2)** API via `get_news()`, introducing advanced categorical filtering (Country, Sector, Corporate Activity, Economic Category, Asset Market) and rich data output. Resolves [#7](https://github.com/smitkunpara/tv-scraper/issues/7).
- **Streaming**: `BaseStreamer` now catching and raising normalized `RuntimeError` for authentication and connection failures.
### Refactor
- **Scanner Migration**: Migrated 8 modules (`Fundamentals`, `Options`, `Markets`, `Technicals`, `Screener`, `MarketMovers`, `SymbolMarkets`, `Calendar`) to inherit from `ScannerScraper`, eliminating thousands of lines of boilerplate and unifying error handling.
- **Social Scrapers**: Refactored `minds.py`, `news.py`, and `pine.py` to use `BaseScraper._request()` for consistent HTTP handling, timeout management, and Captcha detection.
- **Streaming Class Hierarchy**:
  - `Streamer` now correctly extends `BaseStreamer` and delegates to internal sub-streamers.
  - Removed redundant `_get_fresh_handler` implementations, centralizing token resolution in `BaseStreamer.connect()`.
  - Finalized migration of `CandleStreamer` and `ForecastStreamer` to the new architecture.
- **Standardized Dictionaries**: Converted all remaining manual dictionary returns in `streaming/utils.py` and `forecast_streamer.py` to use `_success_response()` and `_error_response()` helpers.

### Fixed
- **Test Suite**: Fixed flakiness in `test_minds.py` rate-limiting tests by adding graceful 1s delays between high-frequency calls.
- **Test Suite**: Corrected API test mocks in `live_api` tests, moving from `requests.post` to `requests.request` to match the new unified network layer.
- **Fundamentals**: Correctly removed deprecated `compare_fundamentals()` in favor of the standardized `get_fundamentals()` scanner logic.
- **IO Utilities**: Fixed a syntax error in `io.py` and restored missing `generate_user_agent` functionality in `helpers.py`.
- **Linting**: Suppressed `PLR0915` (too many statements) in `get_candles` and resolved sorted `__all__` issues across core modules.
- **Error Responses**: `_error_response` now supports passing partial `data` alongside the error message (critical for `get_forecast` timeouts).

### Performance
- **Data Loading**: Significantly reduced `DataValidator` startup time and eliminated disk I/O by migrating static validation data (exchanges, indicators, timeframes, etc.) from JSON files to a consolidated Python module (`validation_data.py`).

### Refactor
- **Core**: Migrated all static validation data from individual JSON files in `tv_scraper/data/` to `tv_scraper/core/validation_data.py`.
- **Core**: Simplified `DataValidator` singleton implementation by removing runtime JSON parsing and file path resolution.
- **Cleanup**: Removed the redundant `tv_scraper/data/` directory and all its JSON contents.

### Removed
- **Auth Module**: **CRITICAL** - Removed dead code: `is_jwt_token_valid()` function was never called
- **Auth Module**: Removed unused `import jwt as pyjwt` import
- **Pine Scraper**: Removed redundant `deleted` field from success response data
- **Options Scraper**: Removed unused `logger` import
- **Options Scraper**: Removed unnecessary `ignore_unknown_fields: False` from payload
- **SymbolMarkets**: Removed unused logging import

### Added
- **Core**: Added timeout validation (must be 1-300 seconds) in BaseScraper.__init__
- **Core**: Added retries validation (must be >= 1) in verify_symbol_exchange
- **Core**: Added thread-safe reset with lock in DataValidator.reset()
- **Core**: Added ScraperResponseSuccess and ScraperResponseFailed TypedDicts with proper Literal constraints
- **Utils**: Added export_type validation with `ALLOWED_EXPORT_TYPES` set
- **Utils**: Added ImportError for pandas to catch missing module
- **Utils**: Added DataFrame type validation before conversion
- **Utils**: Updated docstring with accurate `Raises: ExportError` documentation

### Changed
- **Core**: Moved imports (EXPORT_TYPES, SCANNER_URL, ValidationError, os) to module level in base.py
- **Calendar**: Added `import json` for explicit JSONDecodeError handling
- **Technicals**: Added `import json` for explicit JSON error handling
- **Calendar**: Added `Literal["dividends", "earnings"]` type hint for data_category parameter
- **Calendar**: Added logging for empty results to help debugging
- **Fundamentals**: Added `isinstance(fields, list)` validation for fields parameter
- **Fundamentals**: Added DataValidator field validation for field names
- **Fundamentals**: Added `failed_symbols` tracking for partial failures in `compare_fundamentals()`
- **Market Movers**: Added `language` parameter (default: "en") for configurable language
- **Market Movers**: Added `totalCount` to response metadata (total available in category)
- **Market Movers**: Added user-provided fields validation (list of strings)
- **Market Movers**: Added limit bounds checking (1-1000)
- **News Scraper**: Added `import json` for explicit JSON error handling
- **BaseScraper Enhancements**: Added native cookie support and automatically load the `TRADINGVIEW_COOKIE` environment variable in `BaseScraper.__init__`. All subclasses now benefit from this shared authentication logic.
- **Standardized Exports**: `tv_scraper.core` now correctly exports the base `TvScraperError` exception.
- **Streamer Helpers**: Added `_success_response` and `_error_response` helper methods to the `Streamer` class to maintain API consistency with the scraper modules.
- **Streamer**: Added `BASE_STUDY_ID = 9` constant in utils.py for study ID offset
- **Streamer**: `_error_response` now supports partial data via metadata extraction
- **Ideas Scraper**: Added page validation errors with descriptive messages for invalid page parameters
- **Minds Scraper**: Added `MAX_PAGES = 100` constant to prevent infinite loops during pagination
- **Minds Scraper**: Added separate HTTP error logging for better debugging
- **Auth Module**: Added specific exception types for better token extraction error handling
- **Screener**: Added sort_order validation against `SORT_ORDERS` frozenset
- **Screener**: Added limit bounds checking with `MIN_LIMIT`/`MAX_LIMIT` constants
- **Screener**: Added defensive market validation in `_build_payload()`
- **Pine Scraper**: Extracted input validation to `_validate_non_empty()` helper method
- **Pine Scraper**: Defined `PINE_FILTER_SAVED` constant for magic string "saved"
- **Options Scraper**: Extracted duplicate payload logic to `_build_payload()` helper method
- **Options Scraper**: Added column validation via `_validate_inputs()` method
- **Options Scraper**: Added response structure validation (isinstance checks)
- **Options Scraper**: Added type validation for strike parameter
- **Markets**: Added empty fields list validation
- **Overview**: Fixed ALL_FIELDS to use proper list syntax with unpacking instead of tuple

### Changed
- **Core**: Moved imports (EXPORT_TYPES, SCANNER_URL, ValidationError, os) to module level in base.py
- **Core**: Distinguished error messages in verify_options_symbol for 403 vs not found cases
- **Core**: Removed redundant try-except re-raise in verify_options_symbol
- **Fundamentals**: Renamed `symbol_name` variable to `symbol` for consistency
- **Technicals**: Removed redundant `list()` copy on line 92 (indicators)
- **Technicals**: Removed redundant `list()` copy on line 110 (api_indicators)
- **Technicals**: Removed redundant type hint annotation on line 132
- **Technicals**: Improved empty response error message for better debugging
- **Calendar**: Optimized timestamp calculation by computing `now` and `midnight` once when either timestamp is None
- **Calendar**: Made lang parameter configurable (was hardcoded to "en")
- **Market Movers**: Simplified `_get_sort_config()` by removing unnecessary `dict()` wrapper
- **Market Movers**: Simplified `_resolve_fields()` by removing unnecessary `list()` copy
- **Market Movers**: Separated HTTPError, RequestException, and ValueError/KeyError handlers
- **Network Layer Refactoring**: Successfully migrated all scrapers from the legacy `make_request` utility to direct `requests` library calls (`requests.get`, `requests.post`).
- **News Scraper**: Consolidated `_sort_news()` logic by removing duplicate if/elif branches into single reverse/key pattern
- **News Scraper**: Added JSON parsing error handling (ValueError, JSONDecodeError) for API responses
- **News Scraper**: Added specific exception handlers (HTTPError, Timeout, ConnectionError) for consistent HTTP error handling
- **News Response**: Added `"id": story_id` to `_parse_story()` return for consistency
- **Standardized Error Handling**: Improved network robustness by wrapping all API calls in `try...except requests.RequestException` blocks, ensuring failures always return a valid error envelope rather than raising unhandled exceptions.
- **Metadata Standardization**: Extensively refactored every public method in the library (15+ modules) to ensure the `metadata` field is always present.
  - Enforced `dict[str, Any]` type for all metadata blocks.
  - Dynamically exclude optional arguments (e.g., `area`, `provider`, `filters`) from metadata when they are not provided by the user.
  - Ensured metadata is preserved in both `success` and `failed` status responses for better debugging.
- **Test Suite Modernization**: Refactored over 350 unit and integration tests to verify strict metadata requirements and new standardized response formats.
- **Ideas Scraper**: Made `max_workers` configurable via constructor parameter (default still 3) for concurrent page scraping
- **Ideas Scraper**: Added page validation (start_page/end_page must be positive integers, start <= end)
- **Ideas Scraper**: Added timeout to `as_completed()` and `future.result()` to prevent indefinite hangs
- **Ideas Scraper**: Removed unnecessary `list()` conversion around `range()`
- **Minds Scraper**: Removed redundant early limit check (duplicate validation)
- **Minds Scraper**: Added empty cursor handling (`if not cursor_part: break`)
- **Minds Scraper**: Fixed author URL validation to handle absolute URLs in uri field
- **Auth Module**: Extracted redundant base64 padding logic to `_pad_base64()` helper function
- **Auth Module**: Removed redundant `str()` conversion in token caching
- **Auth Module**: Added empty cookie validation with `cookie.strip()` check
- **Streamer**: Removed redundant boolean flag `ind_flag` by using `indicators` directly
- **Streamer**: Moved `exchange_symbol` variable inside try block
- **Streamer**: Now uses `_error_response` helper for partial forecast data consistency
- **Streamer**: Extracted duplicate timeframe lookup to `_get_mapped_timeframe()` helper method
- **Streamer**: Moved `quote_hibernate_all` outside the loop for efficiency
- **Screener**: Changed OPERATIONS from `list[str]` to `frozenset[str]` and now used for validation
- **Screener**: Added JSON parse error handling (ValueError catch for response.json())
- **Screener**: Separated HTTPError and RequestException handlers for consistent error handling
- **Screener**: Extracted duplicate metadata building to `_build_metadata()` helper method
- **Screener**: Removed unnecessary `list()` copies of class constants
- **Pine Scraper**: Removed redundant `or ""` cookie fallback (self._cookie already handles this)
- **Pine Scraper**: Simplified metadata filtering in error responses
- **Pine Scraper**: Improved `delete_script` error message for better debugging
- **Options Scraper**: Standardized error response metadata
- **Markets**: Added sort_order validation ("asc"/"desc")
- **Markets**: Added limit bounds checking (1-1000)
- **Overview**: Removed redundant `__init__` - now uses inheritance from BaseScraper
- **SymbolMarkets**: Simplified empty check to `if not search_symbol.strip()`
- **Utils**: Inlined root_path variable (removed unnecessary variable)
- **Utils**: Changed bare `except Exception` to `except OSError` for specific exception handling
- **Utils**: Made symbol parameter required (removed empty string handling)

### Fixed
- **Core**: JSON file load now raises exceptions instead of returning empty dict on failure
- **Core**: Added error indicator checks for API responses in _fetch_symbol_fields
- **Core**: Added logging for missing field values in _map_scanner_rows
- **Fundamentals**: Added symbol dict structure validation (must have 'exchange' and 'symbol' keys)
- **Technicals**: **CRITICAL** - Fixed fields filtering bug: Stripping timeframe suffixes now happens AFTER field filtering, not before. This fixes the bug where `fields` parameter didn't work correctly for non-daily timeframes
- **Technicals**: Added `json.JSONDecodeError` to exception handling for explicit JSON parsing error handling
- **Calendar**: **CRITICAL** - Fixed unreachable code: Reordered exception handlers (RequestException → JSONDecodeError → Exception) to make ValueError/KeyError handler reachable
- **Calendar**: Added defensive check `if not isinstance(data_items, list)` for API response validation
- **Calendar**: Fixed redundant None check in metadata building
- **Market Movers**: Added JSON response structure validation (ensures response is a dict)
- **News Scraper**: Added validation for `language` parameter in `get_news_content()` against `_language_codes`
- **News Scraper**: Added empty/whitespace validation for `story_id` parameter
- **News Response**: Fixed duplicate metadata building by extracting shared `meta` dict at start of each method
- **News Response**: Fixed duplicate storyPath normalization by extracting to `_normalize_story_path()` helper
- **Streamer**: **CRITICAL** - Fixed resource leak in `stream_realtime_price()` by adding try/finally block to ensure WebSocket cleanup even on exceptions
- **Streamer**: Added validation for `p_list` before accessing index 1 to prevent potential crashes
- **Streamer**: Added defensive checks for `entry` dict and `v` list to prevent IndexError/KeyError
- **Streamer error handling**: Updated `Streamer.get_candles()` and indicator setup so failures stop execution and return a standardized failed response instead of logging and continuing.
- **Forecast Data**: Fixed `Streamer.get_forecast()` to correctly return partial data in the `data` field when a timeout occurs, ensuring compliance with the documented behavior while maintaining a `failed` status.
- **Pine Metadata**: Removed redundant `source` code from success metadata in `Pine.create_script` and `Pine.edit_script` to reduce response payload size.
- **Ideas Scraper**: **CRITICAL** - Fixed data loss on partial failures: now collects successful results before returning error, instead of discarding all data when some pages fail
- **Ideas Scraper**: Removed unused `json` import and unused `data` variable
- **Ideas Scraper**: Simplified redundant exception handling
- **Minds Scraper**: Added captcha detection (`<title>Captcha Challenge</title>`) to prevent data loss
- **Minds Scraper**: Added JSON parsing error handling (ValueError for response.json())
- **Minds Scraper**: Added `raise_for_status()` for consistent HTTP error handling
- **Auth Module**: Added `OSError` to exception tuple for better WebSocket error handling
- **Auth Module**: Security fix: Generic error message used instead of logging raw error args that could expose JWT tokens
- **Screener**: Added filter structure validation with `_validate_filter()` method
- **Screener**: Added filter2 validation with `_validate_filter2()` method
- **Pine Scraper**: Fixed duplicate warnings check by removing redundant logging and keeping single return path
- **Pine Scraper**: Added scriptIdPart validation in `_extract_save_result()` to prevent empty IDs
- **Pine Scraper**: Added timestamp validation in `_map_script_item()` to prevent invalid values
- **Options Scraper**: Fixed exception handler scope by moving 404 check inside try block
- **Markets**: Added JSON parse error handling (ValueError catch) in both markets.py and symbol_markets.py
- **SymbolMarkets**: Added empty data validation - now returns error instead of empty success for no results
- **Utils**: **CRITICAL** - Fixed race condition in directory creation: Using `exist_ok=True` instead of check-then-create pattern
- **Utils**: **CRITICAL** - Added path traversal protection via `_sanitize_filename_part()` function

## [1.3.2] - 2026-04-03

### Added
- **Authenticated Streaming**: Implemented fully automated JWT extraction and caching via TradingView session cookies. This solves the issue of manual JWT tokens expiring after a few hours and allows for seamless continuous streaming with auto-updating authentication.
- **Auth Module**: New `tv_scraper.streaming.auth` module for secure token resolution.
- **Thread-safe Token Caching**: In-memory caching for resolved JWT tokens with automatic expiry management.

### Changed
- **Removed Parameter**: Deprecated and removed the `websocket_jwt_token` argument from `Streamer.__init__`.
- **Required Option**: Authentication for indicators now exclusively uses the `cookie` parameter which internally resolves the necessary tokens.
- **Utility Refactor**: `fetch_indicator_metadata` now uses the provided session cookies for personal Pine script validation, removing all previously hardcoded placeholders.
- **Streamer**: `get_candles()` now guarantees exactly the requested number of candles by sorting and slicing the final dataset before returning/exporting.
- **Export Behavior**: `get_candles()` now exports the unified `result_data` dictionary (containing both OHLCV and indicators) to a single file, rather than exporting them separately.

### Fixed
- **Indicator Retrieval**: Removed restrictive minimum length check in `Streamer` that prevented capturing indicator data when `numb_candles` was 10 or fewer.
- **Core Validation**: Fixed a bug where `DataValidator` was incorrectly loading timeframe data using the `"indicators"` key.
- **Robustness**: Resolved a potential `UnboundLocalError` in `DataValidator.verify_symbol_exchange` by ensuring correct exception initialization.

### Performance
- **Optimized Lookups**: `DataValidator` now utilizes internal sets for exchanges and indicators, improving validation speed from $O(n)$ to $O(1)$.
- **Thread-Safety**: Implemented `threading.RLock` in `DataValidator` to ensure thread-safe singleton initialization during concurrent access.

### Changed
- **Data Mapping**: Updated `timeframes.json` to rename the top-level key to `"timeframes"` and modernized the `"1d"` mapping to `"1D"`.
- **Technicals Scraper**: Refined `get_technicals` to treat the `"1D"` timeframe as suffix-less, maintaining compatibility with the Scanner API while using the updated `"1D"` mapping.
- **Testing**: Enhanced `test_technicals.py` with specific test cases for Weekly and Monthly timeframe suffixes.

## [1.3.1] - 2026-04-02

### Changed
- Related to [#5](https://github.com/smitkunpara/tv-scraper/issues/5): Add index-based filtering support (`symbols`, `filter2` parameters).

## [1.3.0] - 2026-04-02

### Added
- `Streamer.get_forecast(exchange, symbol, max_packets=...)` for WebSocket-based analyst forecast data on stock symbols.

### Error Handling
- `get_forecast` now returns partial data with a clear missing-keys error when required forecast fields are not fully available within the capture window.

## [1.2.1] - 2026-03-26

### Changed
- Pine list response now preserves script `version` in each `list_saved_scripts()` item, alongside `id`, `name`, and `modified`.

### Documentation
- Updated Pine scraper docs output examples to include `version` for `list_saved_scripts()`.
- Updated Pine + Streamer workflow docs to explicitly show `list_saved_scripts()` as a source of custom indicator `id` + `version` pairs for `Streamer.get_candles()`.

## [1.2.0] - 2026-03-25

### Added
- Pine script management scraper (`tv_scraper.scrapers.scripts.Pine`) with endpoints:
  - `list_saved_scripts()` (GET /pine-facade/list?filter=saved)
  - `validate_script(source)` (POST /pine-facade/translate_light?v=3)
  - `create_script(name, source)` (POST /pine-facade/save/new)
  - `edit_script(pine_id, name, source)` (POST /pine-facade/save/next/{pine_id})
  - `delete_script(pine_id)` (POST /pine-facade/delete/{pine_id})

### Changed
- Pine response format:
  - `create_script` and `edit_script` now return `data.warnings` when compiler warnings exist.
  - `list_saved_scripts` keeps `modified` in list entries.
  - `metadata` is empty when no context is returned.
- Documentation updates:
  - Reordered docs navigation to place Streaming above Scrapers.
  - Standardized `News` scraper docs examples to per-example `code -> output -> details` structure.

### Fixed
- Unified Pine API metadata handling to align with existing scraper conventions.
- `Streamer.get_available_indicators()` now returns standardized response envelope (`status`, `data`, `metadata`, `error`) and propagates upstream fetch errors appropriately.

### Removed
- Removed low-level `RealTimeData` streaming API (`tv_scraper.streaming.price.RealTimeData`).
- Removed RealTimeData public exports from `tv_scraper` and `tv_scraper.streaming`.
- Removed RealTimeData documentation page (`docs/streaming/realtime-price.md`) and related navigation links.
- Removed migration documentation across docs pages, including the standalone `docs/migration-guide.md` page.

## [1.1.0] - 2026-02-20

### ✨ API Standardization & Strict Typing
This major update standardizes the public API across all scrapers with descriptive, discoverable method names (e.g., `get_news()`, `get_minds()`) and enforces strict type safety by requiring separate `exchange` and `symbol` parameters.

### Added
- **Full Type Hinting**: 100% type hint coverage across all modules, satisfying `mypy` strict mode.
- **Strict Generic Types**: Added explicit type parameters to all `dict` and `list` annotations in streaming modules.

### Changed
- **API Standardization**: Standardized primary scraping methods with descriptive names (e.g., `get_technicals()`, `get_fundamentals()`, `get_minds()`, `get_news_headlines()`) across all scraper classes to replace generic `get_data()` or `scrape()` methods.
- **Strict Parameter Passing**: Removed legacy `EXCHANGE:SYMBOL` string parsing. All methods now require `exchange` and `symbol` as distinct, validated parameters.
- **Streaming Refactor**: Substantially cleaned up `RealTimeData` and `Streamer` logic with improved connection handling and type safety.
- **Standardized Response Metadata**: Metadata now consistently returns separate `exchange` and `symbol` keys.

### Fixed
- **Docstring Stubs**: Updated all class-level examples and method documentation to reflect the new API naming conventions.
- **Redundant Logic**: Eliminated duplicate parsing and validation logic in core and streaming layers.

## [1.0.3] - 2026-02-19

### ✨ Unified Validation & Options Stability
This release centralizes all symbol, exchange, and indicator validation into a single core component, eliminating redundancy across the library. It also significantly improves the stability of the Options scraper by adding browser-standard headers to prevent API blocks and fixing result sanitization.

### Added
- **Unified Validation System**: Core `DataValidator.verify_symbol_exchange()` and `verify_options_symbol()` methods for reliable cross-module validation.
- **Browser-Standard Headers**: Standardized HTTP headers for Options searching to ensure 100% success rate and avoid 403 Forbidden errors.

### Changed
- **Validator Migration**: Moved `validate_symbols` out of `streaming.utils` and into `core.validators` to serve as a library-wide singleton.
- **Improved Result Parsing**: Added HTML tag stripping (e.g., `<em>`) for cleaner option search results.
- **Refactored Scrapers**: Updated all scrapers (Technicals, Fundamentals, Overview, etc.) to use the unified validation layer for better performance and consistency.

### Fixed
- **Options Search Block**: Resolved issue where searching for options would return 403 Forbidden on certain environments.
- **Redundant Streaming Code**: Removed duplicate validation logic from `streaming/utils.py`.

## [1.0.2] - 2026-02-16

### 🚀 Initial Production Release
This version transforms the library into a high-performance, industry-standard tool for TradingView data extraction. It introduces a complete architectural refactor with modular design, standardized APIs, comprehensive test coverage, and optimized WebSocket streaming.

### ✨ Highlights
- **Industrial Quality**: Full CI/CD integration, 349 automated tests (89% coverage), and strict type safety.
- **Modern Tooling**: Migrated to `uv`, `ruff`, and `mypy` for a professional developer experience.
- **WebSocket Performance**: Optimized streaming with 4x higher update frequency (~1 update every 3-4s).
- **New Scrapers**: Added `Options` scraper and modernized all legacy modules.

### Added
- **Modern CI/CD Pipeline** — GitHub Actions workflow with matrix testing (Python 3.11, 3.12), Ruff linting, Mypy type checking, and automated test execution
- **Local Workflow Testing** — Makefile with convenient commands (`make check`, `make ci`) for running quality checks locally before pushing
- **Pre-commit Hooks** — Automatic code quality enforcement on every commit with Ruff linting/formatting, trailing whitespace removal, and YAML validation
- **Comprehensive Developer Guide** — `LOCAL_TESTING.md` with complete instructions for local workflow testing, pre-commit setup, and act usage
- **New `tv_scraper` package** with clean modular architecture alongside the legacy `tradingview_scraper` package
- **`Options` scraper** — Fetch option chains by expiration or strike price via TradingView's options scanner API
- **WebSocket Performance Optimizations** — Low-latency streaming with TCP_NODELAY socket option and configurable timeout to prevent indefinite hangs
- **Dual Session Subscription** — Real-time price streaming subscribes to both quote session (QSD) and chart session (DU) for maximum update frequency (~1 update per 3-4 seconds)
- **Enhanced Message Processing** — Added support for DU (data update) messages in addition to QSD messages for faster price updates
- **Comprehensive Live API Tests** — Added `tests/live_api/test_streaming.py` with extensive real-world streaming tests covering multiple timeframes, exchanges, asset types, update frequency verification, connection stability, and edge cases
- **Unit Tests for WebSocket Optimizations** — Added detailed tests for TCP_NODELAY, dual session subscription, mixed message handling, and socket timeout handling
- **Live API smoke tests** — New `tests/live_api/` directory for verifying real-time endpoint availability
- **`Streamer.get_available_indicators()`** — fetch standard built-in indicator IDs and versions for candle streaming
- **12 scraper modules** organized into four categories:
  - Market Data: `Technicals`, `Overview`, `Fundamentals`, `Markets`, `Options`
  - Social: `Ideas`, `Minds`, `News`
  - Screening: `Screener`, `MarketMovers`, `SymbolMarkets`
  - Events: `Calendar`
- **Streaming module** with `Streamer` (OHLC + indicators) and `RealTimeData` (simple OHLCV/watchlist)
- **`BaseScraper` base class** providing standardized response envelopes, HTTP handling, and export logic
- **`DataValidator` singleton** for exchange, indicator, timeframe, and field validation with suggestions
- **Standardized response envelope** (`status`, `data`, `metadata`, `error`) across all scrapers
- **Core exception hierarchy**: `TvScraperError`, `ValidationError`, `DataNotFoundError`, `NetworkError`, `ExportError`
- **Top-level re-exports** — all public classes importable directly from `tv_scraper`
- **265+ unit tests** covering all modules with full mocking (no network calls)
- **50+ live API tests** for comprehensive connectivity verification and streaming performance testing
- **Live connectivity verification tests** for import smoke testing and cross-module verification
- **Comprehensive documentation** with migration guide, API conventions, and per-module docs

### Changed
- **Modern Tooling** — Replaced `flake8` and `pylint` with `Ruff` (10-100x faster) and strict `Mypy` type checking
- **StreamHandler** — Added TCP_NODELAY socket option during WebSocket connection creation to disable Nagle's algorithm for lower latency
- **StreamHandler Reliability** — Added `timeout=10` and `enable_multithread=True` to WebSocket connections to prevent indefinite hangs on half-open connections
- **User-Agent Documentation** — Added explicit comments about keeping User-Agent headers updated to avoid potential blocks
- **Streamer.stream_realtime_price()** — Now subscribes to both quote and chart sessions, processes both QSD and DU message types
- **Socket Timeout Handling** — Added graceful handling of socket.timeout exceptions in streaming generators
- **Unified Parameter Handling** — Standardized `EXCHANGE:SYMBOL` parsing across all core scrapers (`Ideas`, `News`, `Technicals`, `Fundamentals`, `Overview`)
- **API naming conventions**: consistent `get_*` method names (e.g., `get_technicals`, `get_ideas`, `get_news`)
- **Parameter splitting**: exchange and symbol are always separate parameters
- **Error handling**: scrapers return error envelopes instead of raising exceptions
- **Export validation**: invalid `export_type` raises `ValueError` at construction time
- **Cleaned Codebase** — Removed legacy backward compatibility logic for cleaner, more maintainable code
- **Code Formatting** — All source files formatted with Ruff, fixing 258 linting violations for consistent code style

### Performance Improvements
- **WebSocket Update Frequency**: Increased from ~1 update per 15 seconds to ~1 update per 3-4 seconds, matching browser performance
- **Reduced Latency**: TCP_NODELAY eliminates packet transmission delays
- **Enhanced Reliability**: Better handling of network timeouts and connection stability
- **Dual Session Data**: Combines quote and chart session updates for comprehensive real-time market data

### Technical Details
- TCP_NODELAY applied via `sockopt` parameter: `[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]`
- Chart session uses 1-second timeframe for real-time OHLCV updates
- DU messages extract close price and volume from OHLCV arrays: `[timestamp, open, high, low, close, volume]`
- QSD messages provide quote-level data with bid/ask spreads, volume, and percentage changes

### Documentation
- Updated `docs/streaming/index.md` with performance optimization overview
- Updated `docs/streaming/streamer.md` with WebSocket optimization details and dual session strategy
- Updated `docs/streaming/realtime-price.md` with performance notes
- Updated `GEMINI.md` with comprehensive WebSocket implementation details, message types, and testing strategy

### Migration
See `docs_new/migration-guide.md` for the complete migration guide from `tradingview_scraper` to `tv_scraper`.

## [0.5.2] - 2025-12-18

### Overview
This release reintroduces pagination support for the Minds discussions scraper to handle large data requests and improves export functionality reliability.

### Added
- **Pagination Support**: Re-added pagination to `Minds.get_minds()` method to fetch multiple pages of discussions when needed, allowing retrieval of more than the first page's worth of data
- **Cursor-Based Navigation**: Implemented cursor-based pagination using TradingView's API `next` parameter for efficient data fetching

### Changed
- **Minds API**: Modified `get_minds()` to support fetching multiple pages until the requested limit is reached or no more data is available
- **Export Handling**: Moved pandas import inside `save_csv_file()` function for lazy loading, preventing import errors when CSV export is not used

### Fixed
- **Large Limit Handling**: Resolved issues with large limit parameters by implementing proper pagination instead of limiting to first page only
- **Import Errors**: Fixed pandas-related import failures by deferring import until CSV export is actually needed

**Full Changelog**: [Commits](https://github.com/smitkunpara/tv_scraper/commits/v0.5.2)

## [0.5.1] - 2025-12-13

### Overview
This release focuses on simplifying the Minds community discussions scraper by removing pagination and improving packaging for cleaner builds.

### Changed
- **Minds API Refactor**: Simplified `Minds.get_minds()` to fetch only the first page of discussions (removed pagination logic for better reliability and performance)
- **API Simplification**: Removed `sort` parameter and `get_all_minds()` method from Minds scraper
- **Build Backend**: Switched from setuptools to hatchling for modern packaging
- **Build Configuration**: Cleaned up `pyproject.toml` by removing setuptools-specific configuration sections and removed obsolete `MANIFEST.in`
- **Package Exclusions**: Ensured clean builds by relying on `.gitignore` for excluding unwanted files (`.vscode`, `__pycache__`, `dist`, etc.)
- **Dependencies**: Removed `setuptools` from runtime dependencies in `setup.py`
- **Documentation**: Updated MkDocs configuration to use proper icon syntax and cleaned up social links
- **Tests**: Streamlined test suite by removing pagination-related tests and sort validation

### Fixed
- **Packaging**: Ensured clean package builds by properly excluding development and cache files

**Full Changelog**: [Commits](https://github.com/smitkunpara/tv_scraper/commits/v0.5.1)

## [0.5.0] - 2025-12-11

### Overview
This is a major release marking a significant overhaul of the project structure, packaging, and documentation. It introduces modern Python tooling support, improved scraping reliability, and a comprehensive documentation rebuild.

### Added
- Modern Packaging with UV: Completely migrated from requirements.txt to pyproject.toml and uv for faster, more reliable dependency management.
- Python 3.11+ Support: Updated codebase and configuration to fully support and enforce Python 3.11+.
- Documentation Overhaul:
  - Rebuilt documentation site with mkdocs-material for a better reading experience.
  - Added comprehensive guides for Contributing, Installation, and architectural overview (CLAUDE.md).
  - Cleaned up old workflows and added new deployment pipelines.
- Ideas Scraper Refactor:
  - Refactored to use the internal JSON API for better stability.
  - Added threading support for faster data retrieval.
  - Implemented cookie authentication to handle Captcha challenges gracefully.
- Streamer Improvements: Fixed volume data handling and improved return types (returning parsed dicts instead of raw generators in specific contexts).
- News Scraper Enhancements: Improved error logging and captcha handling.

### Fixed
- Critical issues with Captcha challenges by adding proper cookie handling.
- Dependency constraints for python-dotenv.
- Documentation build pipelines.

### Changed
- Removed deprecated pkg_resources in favor of importlib.resources.
- Cleaned up codebase structure for better maintainability.

### Removed
- Outdated GitHub workflows for documentation, release, PyPI deployment, and stale issue management.

**Full Changelog**: [Commits](https://github.com/smitkunpara/tv_scraper/commits/v0.4.21)

## [0.4.20] - 2025-12-10

### Changed
- Refactored ideas scraping to use environment variable only.

### Fixed
- Updated python-dotenv version constraint to >=1.0.1 for Python 3.8 compatibility.
- Updated error message for captcha challenge and added python-dotenv dependency.

## [0.4.19]

### Fixed
- Fix raise error while fetching ideas for pages greater than 1.

## [0.4.17]

### Added
- Add Fundamental Graphs feature for comprehensive financial data.
- Support 9 field categories: income statement, balance sheet, cash flow, profitability, liquidity, leverage, margins, valuation, dividends.
- Helper methods for specific financial statements (get_income_statement, get_balance_sheet, get_cash_flow, etc.).
- Multi-symbol comparison with compare_fundamentals() method.
- Support for 60+ fundamental metrics per symbol.

## [0.4.16]

### Added
- Add Minds feature for community discussions and trading ideas.
- Support recent, popular, and trending sort options.
- Pagination support with get_all_minds() method.
- User engagement metrics (likes, comments) and author information.

## [0.4.15]

### Added
- Add Symbol Overview feature for comprehensive symbol data.
- Support for profile, statistics, financials, performance, and technical data.
- 9 field categories with 70+ data points per symbol.
- Helper methods for specific data categories.

## [0.4.14]

### Added
- Add Markets Overview feature for top stocks analysis.
- Sort by market cap, volume, change, price, volatility.
- Support 9 markets (America, Australia, Canada, Germany, India, UK, Crypto, Forex, Global).

## [0.4.13]

### Added
- Add Symbol Markets feature to find all exchanges/markets where a symbol is traded.
- Support global, regional (America, Crypto, Forex, CFD) market scanners.
- Discover stocks, crypto, derivatives across 100+ exchanges worldwide.

## [0.4.12]

### Added
- Add Screener functionality with custom filters, sorting, and column selection.
- Support 18 markets (America, Canada, Germany, India, UK, Crypto, Forex, CFD, Futures, Bonds, etc.).
- Support 15+ filter operations (greater, less, equal, in_range, crosses, etc.).

## [0.4.11]

### Added
- Add Market Movers scraper (Gainers, Losers, Penny Stocks, Pre-market/After-hours movers).
- Support multiple markets (USA, UK, India, Australia, Canada, Crypto, Forex, Bonds, Futures).

## [0.4.9]

### Added
- Add [documentation](https://mnwato.github.io/tradingview-scraper/).

## [0.4.8]

### Fixed
- Fix bug while fetching ADX+DI indicators.

### Added
- Add timeframe param for streamer export data.

## [0.4.7]

### Fixed
- Fix bug undefined RealTimeData class.

## [0.4.6]

### Added
- Add value argument to specify calendar fields.
- Add Streamer class for getting OHLCV and indicator simultaneously.
- Integrate realtime data and historical exporter into Streamer class.

## [0.4.2]

### Added
- Add calendar (Dividend, Earning).
- Make requirements non-explicit.
- Lint fix.
- Add tests (ideas, realtime_price, indicators).
- Add reconnection method for realtime price scraper.

## [0.4.0]

### Added
- Update exchange list.
- Add real-time price streaming.

## [0.3.2]

### Added
- Support timeframe to get Indicators.

## [0.3.0]

### Added
- Add news scraper.

## [0.2.9]

### Changed
- Refactor for new TradingView structure.

## [0.1.0]

### Changed
- The name of `ClassA` changed to `Ideas`.
