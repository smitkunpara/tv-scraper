## Phase 14 Complete: Final Integration

Assembled all top-level exports, completed documentation suite, added 95 integration tests, bumped version to 1.0.0, and updated CHANGELOG with comprehensive 1.0.0 entry.

**Files created/changed:**
- tv_scraper/__init__.py (updated with 13 public class exports)
- tv_scraper/core/__init__.py (updated with core exports)
- tests_new/integration/__init__.py
- tests_new/integration/test_imports.py (26 import smoke tests)
- tests_new/integration/test_cross_module.py (69 cross-module tests)
- docs_new/index.md
- docs_new/getting-started.md
- docs_new/migration-guide.md (complete rewrite)
- pyproject.toml (version 1.0.0, pytest-cov, hatch build config)
- CHANGELOG.md (1.0.0 entry)

**Functions created/changed:**
- tv_scraper.__init__: __all__ with 13 exports
- tv_scraper.core.__init__: __all__ with 11 core exports

**Tests created/changed:**
- TestTopLevelImports: 13 tests
- TestSubpackageImports: 5 tests
- TestCoreImports: 4 tests
- TestVersionAndAll: 4 tests
- TestScraperInheritance: parametrized (11 classes)
- TestResponseMethods: parametrized (11 classes)
- TestConstructorParams: parametrized (11 classes)
- TestExportTypeValidation: parametrized (11 classes)
- TestResponseEnvelope: parametrized (11 classes)
- TestDataValidatorSingleton: 3 tests
- TestMakeRequest: 2 tests
- Total: 95 integration tests, 333 total suite

**Review Status:** APPROVED

**Git Commit Message:**
feat: final integration and v1.0.0 release preparation
