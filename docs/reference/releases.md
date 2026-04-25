# Releases & Versioning

This project is set up to use versioned MkDocs builds with `mike`, so readers can switch between released docs when those versions are published to GitHub Pages.

## What Readers Should Expect

- The deployed site should offer a version switcher in the header.
- `latest` should point to the newest stable branch build.
- tagged releases such as `v1.3.2` or `v1.4.0` should appear as their own docs versions.

## Docs Availability

The documentation site was introduced in **`v0.5.0`**. That means the release-aware docs story starts from `v0.5.0` onward.

## Known Versions In This Repository

| Version |
|---------|
| `v0.5.0` |
| `v0.5.1` |
| `v0.5.2` |
| `v1.0.0` |
| `v1.0.2` |
| `v1.0.3` |
| `v1.1.0` |
| `v1.2.0` |
| `v1.2.1` |
| `v1.3.0` |
| `v1.3.1` |
| `v1.3.2` |
| `v1.4.0` |
| `v1.4.1` |
| `v1.4.2` |
| `v1.4.3` |

## Current Docs Target

The current package version is **`1.4.3`**.

## Publishing Notes

For maintainers:

- branch builds should publish the moving alias such as `latest`
- tag builds should publish the exact release version
- older tags may need a backfill pass if they were created before the version switcher config was added

If repo instructions or contributor workflow docs still describe a non-versioned docs flow, update them alongside the docs changes.
