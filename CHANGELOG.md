# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- Split GitHub relevance matching into separate Product News and Changelog rules so product posts can trust official AI-oriented labels and full article content without making changelog filtering overly broad

## [0.6.2] - 2026-04-09

### Changed
- Expanded GitHub coverage by evaluating changelog entries against full post content instead of only short feed descriptions, which pulls in more developer-facing Copilot, Actions, and intelligent security workflow updates

### Fixed
- Tightened GitHub relevance matching so generic platform-maintenance notices are excluded while developer-relevant Copilot and smart security workflow releases remain included

## [0.6.1] - 2026-04-09

### Fixed
- Replaced the fragile theme-toggle SVG with stable sun and crescent symbols so the header icon renders correctly in both light and dark themes
- Backfilled stale Chinese localizations whose `zh` fields still matched English, and updated translation handling so untranslated locale values are regenerated instead of being preserved as-is

## [0.6.0] - 2026-04-09

### Changed
- Renamed the old `microsoft` category and UI language to `GitHub` because the dataset currently contains GitHub-only sources rather than Microsoft-wide sources
- Expanded Google coverage to include product-focused posts from Google DeepMind in addition to Google Blog and Google Cloud release notes

### Fixed
- Normalized official source URLs during digest rebuilds so trailing-slash variants no longer create duplicate Google and GitHub entries

## [0.5.1] - 2026-04-09

### Fixed
- Simplified the theme toggle back to a clear icon-only control, keeping the moon visible in light mode and the sun visible in dark mode without an extra text label

## [0.5.0] - 2026-04-09

### Changed
- Expanded automated ingestion beyond marketing news pages to include official developer release notes and changelogs for Anthropic, OpenAI, Google, and GitHub
- The digest rebuild now captures product and API updates that may appear in docs or changelog surfaces before or instead of blog-style news posts
- The homepage now labels each item as News, Changelog, or Release Notes, and low-quality auto-generated titles are normalized during rebuilds
- GitHub Actions refreshes now fail closed on suspicious digest drops or missing required sources, and publish per-run source summaries for easier debugging
- Validation thresholds are now configurable from the GitHub Actions workflow instead of being hard-coded in the script
- Newly fetched English-only entries are now automatically translated into Chinese and Japanese during digest rebuilds, with translations cached for later runs
- The header theme toggle now uses an explicit labeled control instead of a barely recognizable icon-only button
- Language switching is now consistent across the digest because English-only auto-filled entries are translated during refresh instead of being written unchanged into every locale field

## [0.4.0] - 2026-04-09

### Added
- Month-based filtering on the homepage in addition to source filters and full-text search
- Automated digest refresh via GitHub Actions using only official source pages and feeds
- Rolling 3-month retention with `data/archive.json` for older items
- Repository script `scripts/update_digest.py` to fetch, deduplicate, preserve translations, and rebuild datasets

### Changed
- `README.md` now documents the automation workflow, schedule, retention rules, and archive behavior
- `data/digest.json` is now intended to be machine-refreshed from official sources instead of maintained as a fixed manual snapshot

## [0.3.0] - 2026-04-09

### Changed
- **News data rebuilt from official sources** — All items now sourced from the four official channels:
  - [Anthropic News](https://www.anthropic.com/news)
  - [OpenAI News](https://openai.com/news/company-announcements/)
  - [Google Gemini Blog](https://blog.google/products-and-platforms/products/gemini/)
  - [GitHub Product News](https://github.blog/news-insights/product-news/)
- 14 real, verified news items with accurate URLs and dates

### Added
- `README.md` — Project overview, structure, data format, and contribution guide
- `CHANGELOG.md` — This file
- `CONTRIBUTING.md` — Contribution guidelines
- `LICENSE` — MIT license
- `.gitignore`

## [0.2.0] - 2026-04-09

### Added
- **Trilingual support (中文 / 日本語 / English)** — Language switcher in header
- News titles and summaries in all three languages
- UI elements (stats, filters, search placeholder, footer) fully translated
- Language preference saved to `localStorage`

### Changed
- `digest.json` schema: `title` and `summary` changed from string to `{zh, ja, en}` object

## [0.1.1] - 2026-04-09

### Fixed
- Theme toggle icon invisible in light mode — forced high-contrast colors

## [0.1.0] - 2026-04-09

### Added
- Initial release
- Dark / light theme toggle
- Filter by company (Microsoft, Anthropic, OpenAI, Google)
- Full-text search across titles, summaries, and tags
- Responsive design
- GitHub Pages deployment
