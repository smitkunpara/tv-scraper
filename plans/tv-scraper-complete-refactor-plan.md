# Plan: TV Scraper Complete Refactor to `tv_scraper` v1.0.0

**Created:** 2026-02-15
**Status:** Ready for Atlas Execution

## Summary

This plan delivers a full, non-destructive refactor from `tradingview_scraper/` to a brand-new `tv_scraper/` package using a strict module-by-module workflow. The implementation preserves existing business logic while standardizing architecture, API surface, naming conventions, response envelopes, validation, tests, and documentation. Work proceeds sequentially through 14 tasks: core architecture, 11 scraper modules, streaming, then integration/release hardening. Legacy folders (`tradingview_scraper/`, `tests/`, `docs/`) remain untouched throughout.

## Context & Analysis

**Relevant Files:**
- `tradingview_scraper/symbols/utils.py`: shared export helpers, user agent generation, symbol/list validators, data loaders to be split into `tv_scraper/core` + `tv_scraper/utils`.
- `tradingview_scraper/symbols/exceptions.py`: current custom exception baseline (`DataNotFoundError`).
- `tradingview_scraper/symbols/*.py`: source of module logic to preserve while standardizing signatures/output.
- `tradingview_scraper/symbols/stream/*.py`: source for streaming refactor and realtime feature extension.
- `tradingview_scraper/data/*.txt|json`: source data for conversion into `tv_scraper/data/*.json`.
- `tests/test_*.py`: legacy behavior reference to port into `tests_new/`.
- `docs/*.md`: legacy docs reference to rewrite into `docs_new/`.
- `pyproject.toml`: version/package metadata update to `1.0.0` and packaging scope.
- `mkdocs.yml`: docs navigation strategy and docs path implications.
- `README.md`: migration of examples/imports to new namespace.

**Key Functions/Classes:**
- `Ideas.scrape(...)` in `tradingview_scraper/symbols/ideas.py`: camelCase params + list return; must standardize.
- `Indicators.scrape(...)` in `tradingview_scraper/symbols/technicals.py`: split symbol inputs already present; rename params.
- `Overview.get_symbol_overview(...)` and helper category methods in `overview.py`: combined symbol input currently required.
- `FundamentalGraphs.get_fundamentals(...)` and `compare_fundamentals(...)` in `fundamental_graphs.py`: combined symbol flow and compare behavior.
- `Markets.get_top_stocks(...)`, `Screener.screen(...)`, `MarketMovers.scrape(...)`, `SymbolMarkets.scrape(...)`: scanner payload mapping with parameter inconsistencies (`columns`, `by`).
- `CalendarScraper.scrape_dividends(...)` / `scrape_earnings(...)` in `cal.py`: `values` naming and list-return behavior.
- `Streamer.stream(...)`, `RealTimeData.get_ohlcv(...)`, `StreamHandler` in `stream/*`: rename/feature additions and persistence semantics.

**Dependencies:**
- `requests`, `pandas`, `beautifulsoup4`, `websocket-client`, `websockets`, `python-dotenv` from `pyproject.toml`.
- Existing build backend: `hatchling`.
- Existing test stack: `pytest`, `pytest-mock`.
- Existing docs toolchain: `mkdocs`, `mkdocs-material`.

**Patterns & Conventions:**
- Existing modules often use `export_result` + `export_type`; this should centralize in `BaseScraper`.
- Error handling is inconsistent today (raise vs failed dict vs empty list); new contract must always return standardized response dict in scraper methods.
- Input signatures vary (combined `EXCHANGE:SYMBOL`, plain symbol, split params); new standard is always `exchange: str, symbol: str`.
- Parameter names vary (`columns`, `values`, `startPage`, `allIndicators`); new naming must be snake_case + canonical fields/sort.
- Tests currently mix unit/integration behavior; `tests_new` must isolate module-specific unit runs during module tasks.

## Hard Constraints

- Do not modify existing files in:
  - `tradingview_scraper/`
  - `tests/`
  - `docs/`
- Build all new implementation in:
  - `tv_scraper/`
  - `tests_new/`
  - `docs_new/`
- Execute strictly in sequence (Task 1 → Task 14), no module parallelization.

## Implementation Phases

### Phase 1: Architecture Foundation (Task 1)

**Objective:** Create the reusable foundation (`core`, `utils`, `data`, base docs, and core tests) for all subsequent modules.

**Files to Modify/Create:**
- `tv_scraper/__init__.py`
- `tv_scraper/core/__init__.py`
- `tv_scraper/core/base.py`
- `tv_scraper/core/validators.py`
- `tv_scraper/core/constants.py`
- `tv_scraper/core/types.py`
- `tv_scraper/core/exceptions.py`
- `tv_scraper/utils/__init__.py`
- `tv_scraper/utils/io.py`
- `tv_scraper/utils/http.py`
- `tv_scraper/utils/helpers.py`
- `tv_scraper/data/exchanges.json`
- `tv_scraper/data/indicators.json`
- `tv_scraper/data/timeframes.json`
- `tv_scraper/data/languages.json`
- `tv_scraper/data/areas.json`
- `tv_scraper/data/news_providers.json`
- `docs_new/migration-guide.md`
- `docs_new/architecture.md`
- `docs_new/api-conventions.md`
- `tests_new/unit/test_core/test_base_scraper.py`
- `tests_new/unit/test_core/test_validators.py`
- `tests_new/unit/test_core/test_response_format.py`

**Tests to Write:**
- `test_base_scraper.py`: init defaults, export routing, request wrapper timeout handling, success/error builders.
- `test_validators.py`: singleton loading/caching, exchange/symbol/indicator/timeframe validation and suggestion messages.
- `test_response_format.py`: contract schema for success/failed responses and metadata consistency.

**Steps:**
1. Create package skeleton and core interfaces/types first.
2. Write core tests for response schema, validator behaviors, and BaseScraper wrappers (expected to fail).
3. Implement `BaseScraper`, `DataValidator`, constants, and utility modules with timeout default `10`.
4. Convert txt catalogs to JSON with metadata fields and wire validator to load once at import.
5. Run only core tests (`pytest tests_new/unit/test_core -v`) until green; polish docs_new base pages.

**Acceptance Criteria:**
- [ ] `tv_scraper/core/` complete with reusable base architecture.
- [ ] All required `tv_scraper/data/*.json` present and loadable.
- [ ] Base documentation in `docs_new/` exists and reflects v1 API conventions.
- [ ] `tests_new/unit/test_core/*` pass.
- [ ] No changes in legacy folders.

---

### Phase 2: Technicals Module (Task 2)

**Objective:** Refactor technical indicators module to new path + standardized API/response.

**Files to Modify/Create:**
- `tv_scraper/scrapers/__init__.py`
- `tv_scraper/scrapers/market_data/__init__.py`
- `tv_scraper/scrapers/market_data/technicals.py`
- `docs_new/scrapers/technicals.md`
- `tests_new/unit/test_technicals.py`

**Tests to Write:**
- Preserve legacy scenarios from `tests/test_indicators.py`.
- Add tests for renamed params (`all_indicators`, `technical_indicators`) and standardized response envelope.
- Add validation tests ensuring no exceptions leak from scraper methods.

**Steps:**
1. Port and rewrite module tests for the new API (fail first).
2. Implement `Technicals` scraper inheriting `BaseScraper`.
3. Rename/normalize params: `allIndicators -> all_indicators`, `indicators -> technical_indicators` while preserving `fields` convention for selected output fields.
4. Standardize failed responses for invalid exchange/timeframe/indicator.
5. Run only `pytest tests_new/unit/test_technicals.py -v` and update docs.

**Acceptance Criteria:**
- [ ] New technicals module uses `exchange`, `symbol` split input.
- [ ] Standard response envelope used for success and failure.
- [ ] Module tests pass in isolation.

---

### Phase 3: Overview Module (Task 3)

**Objective:** Refactor overview scraper to split symbol input and standardized base architecture.

**Files to Modify/Create:**
- `tv_scraper/scrapers/market_data/overview.py`
- `docs_new/scrapers/overview.md`
- `tests_new/unit/test_overview.py`

**Tests to Write:**
- Port coverage from `tests/test_overview.py`.
- Add tests ensuring all helper methods accept `exchange`, `symbol` separately.
- Validate response format and failed-path semantics.

**Steps:**
1. Write/port tests for split params and envelope output (expected fail).
2. Implement overview logic on top of `BaseScraper` + `DataValidator`.
3. Maintain existing field category behavior (`profile`, `statistics`, etc.) with new signature.
4. Ensure all errors return `_error_response()`.
5. Run `pytest tests_new/unit/test_overview.py -v`; finalize docs.

**Acceptance Criteria:**
- [ ] No combined symbol input required.
- [ ] Helper methods preserved with updated signatures.
- [ ] Isolated module tests pass.

---

### Phase 4: Fundamentals Module (Task 4)

**Objective:** Refactor `fundamental_graphs` into `fundamentals` with split symbol inputs and standardized output.

**Files to Modify/Create:**
- `tv_scraper/scrapers/market_data/fundamentals.py`
- `docs_new/scrapers/fundamentals.md`
- `tests_new/unit/test_fundamentals.py`

**Tests to Write:**
- Port scenarios from `tests/test_fundamental_graphs.py`.
- Add tests for new import/module name and response envelope consistency.
- Cover compare behavior with explicit metadata.

**Steps:**
1. Port tests to new module path/name (fail first).
2. Implement fundamentals scraper inheriting `BaseScraper`.
3. Replace combined symbol requirements with `exchange`, `symbol`.
4. Preserve field category and compare logic behavior.
5. Run `pytest tests_new/unit/test_fundamentals.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Module renamed and importable as `fundamentals`.
- [ ] Standardized input/output conventions applied.
- [ ] Isolated tests pass.

---

### Phase 5: Markets Module (Task 5)

**Objective:** Refactor markets scraper with canonical `fields`, `sort_by`, `sort_order` contract.

**Files to Modify/Create:**
- `tv_scraper/scrapers/market_data/markets.py`
- `docs_new/scrapers/markets.md`
- `tests_new/unit/test_markets.py`

**Tests to Write:**
- Port all relevant scenarios from `tests/test_markets.py`.
- Add tests for `columns -> fields` and `by -> sort_by` mapping.
- Add tests confirming validation errors return failed response dicts.

**Steps:**
1. Port tests with renamed parameters (fail first).
2. Implement module with `BaseScraper` request/response/export helpers.
3. Normalize output metadata keys (`total_count`, limit, sort context).
4. Remove exception leakage from validators.
5. Run `pytest tests_new/unit/test_markets.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Canonical naming (`fields`, `sort_by`, `sort_order`) in public API.
- [ ] Response envelope uniform across success/failure.
- [ ] Isolated tests pass.

---

### Phase 6: Ideas Module (Task 6)

**Objective:** Refactor ideas scraper to include exchange input, snake_case paging, and standardized response.

**Files to Modify/Create:**
- `tv_scraper/scrapers/social/__init__.py`
- `tv_scraper/scrapers/social/ideas.py`
- `docs_new/scrapers/ideas.md`
- `tests_new/unit/test_ideas.py`

**Tests to Write:**
- Port behaviors from `tests/test_ideas.py`.
- Add tests for `exchange` + `symbol` handling and page-range args (`start_page`, `end_page`).
- Add tests for standardized sort options and failed response contract.

**Steps:**
1. Translate legacy tests to new API names/signatures.
2. Implement module preserving scraping logic and pagination/threading behavior.
3. Standardize response to envelope (`status`, `data`, `metadata`, `error`).
4. Convert silent empties for invalid input to meaningful failed responses.
5. Run `pytest tests_new/unit/test_ideas.py -v`; finalize docs/migration notes.

**Acceptance Criteria:**
- [ ] Ideas now requires `exchange`, `symbol` split inputs.
- [ ] camelCase params fully removed.
- [ ] Isolated tests pass.

---

### Phase 7: Minds Module (Task 7)

**Objective:** Refactor minds scraper with split symbol input and consistent pagination/output conventions.

**Files to Modify/Create:**
- `tv_scraper/scrapers/social/minds.py`
- `docs_new/scrapers/minds.md`
- `tests_new/unit/test_minds.py`

**Tests to Write:**
- Port from `tests/test_minds.py`.
- Add tests for split `exchange`, `symbol` and `limit` behavior.
- Add tests for standardized failed response semantics.

**Steps:**
1. Port tests and adapt fixtures/mocks.
2. Implement refactored module using `BaseScraper` + `DataValidator`.
3. Preserve cursor pagination/data normalization logic.
4. Standardize no-data and error responses.
5. Run `pytest tests_new/unit/test_minds.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Split symbol params and response envelope fully standardized.
- [ ] Pagination behavior retained.
- [ ] Isolated tests pass.

---

### Phase 8: News Module (Task 8)

**Objective:** Refactor news scraper with consistent response format and non-raising scraper methods.

**Files to Modify/Create:**
- `tv_scraper/scrapers/social/news.py`
- `docs_new/scrapers/news.md`
- `tests_new/unit/test_news.py`

**Tests to Write:**
- Port from `tests/test_news.py`.
- Add tests for consistent failed responses across all invalid filter combinations.
- Add tests for content scraping methods and metadata in response envelope.

**Steps:**
1. Port test scenarios and add explicit error-schema assertions.
2. Implement module with existing business logic and validator-backed filter checks.
3. Convert all raises in public scraper methods to `_error_response()`.
4. Normalize naming with `sort_by`, `sort_order`, snake_case.
5. Run `pytest tests_new/unit/test_news.py -v`; update docs.

**Acceptance Criteria:**
- [ ] No public scraper method raises on validation/runtime errors.
- [ ] Response envelope used for headlines and content flows.
- [ ] Isolated tests pass.

---

### Phase 9: Screener Module (Task 9)

**Objective:** Refactor screener module to canonical `fields` naming and standardized errors.

**Files to Modify/Create:**
- `tv_scraper/scrapers/screening/__init__.py`
- `tv_scraper/scrapers/screening/screener.py`
- `docs_new/scrapers/screener.md`
- `tests_new/unit/test_screener.py`

**Tests to Write:**
- Port from `tests/test_screener.py`.
- Add tests for `columns -> fields` transition.
- Add tests for sort and filter validation response consistency.

**Steps:**
1. Rewrite tests for new API and envelope behavior.
2. Implement screener module with standardized args and metadata.
3. Replace pre-validation raises with failed response dicts.
4. Confirm field mapping and scanner payload generation remain equivalent.
5. Run `pytest tests_new/unit/test_screener.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Public API uses `fields` exclusively.
- [ ] Sort/filter behavior preserved with standardized errors.
- [ ] Isolated tests pass.

---

### Phase 10: Market Movers Module (Task 10)

**Objective:** Refactor market movers module while preserving category behavior and standardizing response/errors.

**Files to Modify/Create:**
- `tv_scraper/scrapers/screening/market_movers.py`
- `docs_new/scrapers/market_movers.md`
- `tests_new/unit/test_market_movers.py`

**Tests to Write:**
- Port from `tests/test_market_movers.py`.
- Add tests for category validation and standardized failed response.
- Add tests for default fields + limit handling.

**Steps:**
1. Port tests with response-contract assertions.
2. Implement module inheriting `BaseScraper`.
3. Preserve existing category-to-filter/sort semantics.
4. Normalize validation handling to return errors (not raise).
5. Run `pytest tests_new/unit/test_market_movers.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Category behavior retained.
- [ ] Errors standardized to response dict.
- [ ] Isolated tests pass.

---

### Phase 11: Symbol Markets Module (Task 11)

**Objective:** Refactor symbol markets module to canonical naming and standardized metadata keys.

**Files to Modify/Create:**
- `tv_scraper/scrapers/screening/symbol_markets.py`
- `docs_new/scrapers/symbol_markets.md`
- `tests_new/unit/test_symbol_markets.py`

**Tests to Write:**
- Port from `tests/test_symbol_markets.py`.
- Add tests for `columns -> fields` and scanner validation.
- Add tests for normalized metadata keys (`total_count`).

**Steps:**
1. Translate tests to new API naming.
2. Implement module on top of base architecture.
3. Preserve query and result matching behavior.
4. Standardize response metadata naming and error policy.
5. Run `pytest tests_new/unit/test_symbol_markets.py -v`; update docs.

**Acceptance Criteria:**
- [ ] API uses `fields`, snake_case, standardized metadata.
- [ ] Scanner validation returns failed envelope.
- [ ] Isolated tests pass.

---

### Phase 12: Calendar Module (Task 12)

**Objective:** Refactor calendar scraper with canonical `fields` parameter and standardized output.

**Files to Modify/Create:**
- `tv_scraper/scrapers/events/__init__.py`
- `tv_scraper/scrapers/events/calendar.py`
- `docs_new/scrapers/calendar.md`
- `tests_new/unit/test_calendar.py`

**Tests to Write:**
- Port scenarios from `tests/test_cal.py` + relevant index mapping behavior from `tests/test_utils.py`.
- Add tests for `values -> fields` renaming.
- Add tests for response envelope and metadata (date windows, market filters).

**Steps:**
1. Port tests and enforce new API names.
2. Implement `Calendar` module preserving dividends/earnings transformations.
3. Replace raised errors with failed responses in public methods.
4. Keep date default behavior and field filtering semantics.
5. Run `pytest tests_new/unit/test_calendar.py -v`; update docs.

**Acceptance Criteria:**
- [ ] Calendar public API uses `fields` parameter.
- [ ] Public methods return standardized response dicts.
- [ ] Isolated tests pass.

---

### Phase 13: Streaming Refactor + Realtime Feature (Task 13)

**Objective:** Refactor streaming package, rename misleading method, and add persistent realtime price streaming API.

**Files to Modify/Create:**
- `tv_scraper/streaming/__init__.py`
- `tv_scraper/streaming/stream_handler.py`
- `tv_scraper/streaming/streamer.py`
- `tv_scraper/streaming/price.py`
- `tv_scraper/streaming/utils.py`
- `docs_new/streaming/index.md`
- `docs_new/streaming/streamer.md`
- `docs_new/streaming/realtime-price.md`
- `tests_new/unit/test_streaming.py`

**Tests to Write:**
- Port critical behavior from `tests/test_streamer.py` and `tests/test_realtime_price.py` into deterministic unit tests with websocket mocking.
- Add tests for renamed API:
  - `Streamer.get_candles(...)` (replacement for legacy `stream(...)` behavior).
  - `Streamer.stream_realtime_price(exchange, symbol)` generator semantics.
- Add tests ensuring single persistent connection behavior and heartbeat handling.

**Steps:**
1. Write unit tests for `get_candles` and `stream_realtime_price` first (fail expected).
2. Implement renamed methods and compatibility alias (`stream -> get_candles`) if needed for migration ergonomics.
3. Add persistent realtime generator that reuses one connection/session and yields normalized price updates continuously.
4. Standardize split `exchange`, `symbol` inputs and error response policy.
5. Run `pytest tests_new/unit/test_streaming.py -v`; complete streaming docs.

**Acceptance Criteria:**
- [ ] `get_candles()` exists and preserves candle retrieval behavior.
- [ ] `stream_realtime_price()` exists and streams updates continuously.
- [ ] Streaming tests pass in isolation.

---

### Phase 14: Final Integration, Packaging, and Release Readiness (Task 14)

**Objective:** Assemble clean exports, complete docs/test integration, validate no-touch constraints, and prepare v1.0.0 release.

**Files to Modify/Create:**
- `tv_scraper/__init__.py`
- `tv_scraper/scrapers/market_data/__init__.py`
- `tv_scraper/scrapers/social/__init__.py`
- `tv_scraper/scrapers/screening/__init__.py`
- `tv_scraper/scrapers/events/__init__.py`
- `tv_scraper/streaming/__init__.py`
- `docs_new/index.md`
- `docs_new/getting-started.md`
- `docs_new/migration-guide.md` (finalized)
- `docs_new/api-reference/*`
- `tests_new/integration/*`
- `pyproject.toml`
- `CHANGELOG.md`

**Tests to Write:**
- Cross-module integration workflows in `tests_new/integration/`.
- Import smoke tests for all top-level exports.
- Docs example smoke tests where practical.

**Steps:**
1. Finalize top-level exports exactly per target API and verify import graph.
2. Complete docs_new landing/start/migration/reference pages with v1 imports/examples.
3. Add integration tests and run full new suite:
   - `pytest tests_new/ -v`
   - `pytest tests_new/ --cov=tv_scraper`
4. Verify `tradingview_scraper/`, `tests/`, `docs/` unchanged (diff check).
5. Update `pyproject.toml` to version `1.0.0`, adjust package naming/inclusion if needed, and document breaking changes in `CHANGELOG.md`.

**Acceptance Criteria:**
- [ ] New package exports match target API surface.
- [ ] New docs are complete and aligned with code.
- [ ] Full `tests_new` suite passes with >=85% coverage.
- [ ] Legacy folders are untouched.
- [ ] Version bumped to `1.0.0` and changelog reflects breaking changes.

## Module Completion Checklist

**Architecture (Task 1):**
- [ ] Core infrastructure created
- [ ] Validators implemented
- [ ] Data files converted
- [ ] Base docs written
- [ ] Core tests passing

**Market Data Scrapers:**
- [ ] Task 2: Technicals
- [ ] Task 3: Overview
- [ ] Task 4: Fundamentals
- [ ] Task 5: Markets

**Social Scrapers:**
- [ ] Task 6: Ideas
- [ ] Task 7: Minds
- [ ] Task 8: News

**Screening Scrapers:**
- [ ] Task 9: Screener
- [ ] Task 10: Market Movers
- [ ] Task 11: Symbol Markets

**Events & Streaming:**
- [ ] Task 12: Calendar
- [ ] Task 13: Streaming

**Final Integration:**
- [ ] Task 14: Integration, docs, full tests, release prep

## Open Questions

1. Should legacy import compatibility shims be provided (`tradingview_scraper` -> `tv_scraper`) during v1 rollout?
   - **Option A:** No shim (hard break, cleaner architecture).
   - **Option B:** Add temporary shim with deprecation warnings.
   - **Recommendation:** Option B for one minor cycle to reduce migration friction.

2. Should `Streamer.stream` remain as deprecated alias to `get_candles`?
   - **Option A:** Remove immediately in v1.0.0.
   - **Option B:** Keep alias with deprecation warning through v1.x.
   - **Recommendation:** Option B to avoid unnecessary breakage for current users.

3. Package metadata naming strategy in `pyproject.toml`:
   - **Option A:** Keep distribution name `tradingview-scraper`, expose new module namespace only.
   - **Option B:** Publish under new distribution name aligned with `tv_scraper`.
   - **Recommendation:** Option A initially (safer continuity), revisit Option B in a dedicated packaging migration.

## Risks & Mitigation

- **Risk:** Behavior drift while renaming parameters and standardizing responses.
  - **Mitigation:** TDD-first per module; port legacy scenarios before implementation changes.

- **Risk:** Live API instability in tests causing flaky CI.
  - **Mitigation:** Keep module tasks unit-focused with mocks; isolate live calls to `tests_new/integration` only.

- **Risk:** Streaming regressions due to persistent websocket changes.
  - **Mitigation:** Add deterministic websocket fixture/mocks and explicit heartbeat/cleanup tests.

- **Risk:** Accidental changes to legacy folders.
  - **Mitigation:** Add per-task diff gate to assert only `tv_scraper/`, `tests_new/`, `docs_new/`, and approved meta files changed.

- **Risk:** Docs/API drift during long sequential migration.
  - **Mitigation:** Require docs update + module test pass as exit criteria for every phase.

## Success Criteria

- [ ] All 14 phases complete sequentially.
- [ ] Every new scraper inherits base architecture and uses standardized conventions.
- [ ] New streaming API includes `get_candles` and `stream_realtime_price`.
- [ ] `tests_new` full suite passes with >=85% coverage.
- [ ] `tv_scraper` package and docs are release-ready for `1.0.0`.
- [ ] Legacy implementation and legacy docs/tests remain untouched.

## Notes for Atlas

- Execute exactly phase-by-phase in the order above; no parallel module work.
- For each phase: write tests first, run only phase-specific tests, implement minimal changes to pass, then update docs.
- After each phase, run code review subagent and resolve high-confidence review findings before moving forward.
- Keep commits granular per task (`feat/refactor/test/docs` conventional messages).
- Preserve business logic unless explicitly called out in this plan; prioritize structural/API standardization over feature changes.