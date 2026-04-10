# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.2] - 2026-04-10

### Changed
- Redistributed the five daily GitHub Actions refresh times evenly across 24 hours (~4 h 48 min apart) and offset from the hour mark to reduce scheduling contention

## [1.1.1] - 2026-04-10

### Fixed
- "Today" stat always showed 0 because it compared against the current UTC date, which rarely matched any digest entry; now shows the count for the most recent date in the data and relabeled to "Latest" / "最新"

## [1.1.0] - 2026-04-09

### Added
- Source type filter row (News / Changelog / Release Notes) below the company filter, with dynamic counts that reflect the active company selection and vice versa
- Back-to-top floating button in the bottom-right corner, appears after scrolling 400px
- Month sidebar navigator fixed on the left (screens ≥ 1280px), highlights the current scroll position and supports click-to-jump
- Translation now protects ~40 proper nouns (Claude, Gemini, Copilot, Vertex AI, etc.) with placeholders before sending to Google Translate, preventing mistranslations like “克劳德” for Claude or “双子座” for Gemini

### Fixed
- Logo link changed from `/` to `./` to prevent 404 on GitHub Pages sub-path deployments
- Footer disclaimer updated to remove “manual” — data is now fully automated
- Source type filter button styling fixed with `appearance: none` reset for cross-browser consistency
- Cleared and regenerated all previously mistranslated entries in digest data and translation cache

## [1.0.0] - 2026-04-09

### Changed
- Anthropic News scraper rewritten to discover articles via sitemap.xml and extract metadata from individual article pages, replacing the fragile front-page HTML regex that only captured ~12 items; coverage tripled from ~12 to ~35 articles
- Google DeepMind scraper switched from HTML card parsing to the official RSS feed at deepmind.google/blog/rss.xml, eliminating per-article fetches and improving reliability
- Broadened Google Blog keyword filter to include AI Studio, NotebookLM, AI Overviews, AI Mode, Workspace AI, Circle to Search, Project Astra, Project Mariner, and Jules
- Broadened Google Cloud Release Notes filter to include Vertex AI Search, Agent Builder, context caching, batch prediction, Model Garden, function calling, tuning, multimodal, embeddings, and more
- Broadened Google DeepMind filter with additional product keywords (AlphaFold, AlphaCode, AlphaProof, AlphaGeometry, Trillium, Nano Banana, NotebookLM, AI Studio) while keeping pure-research/safety posts filtered
- Removed unused resolve_anthropic_url helper

## [0.9.0] - 2026-04-09

### Added
- Interactive trend chart at the top of the page showing monthly update frequency per company (GitHub / Anthropic / OpenAI / Google) as color-coded line chart
- Chart uses Chart.js via CDN, auto-aggregates from existing digest data, and updates dynamically with theme and language switches

## [0.8.0] - 2026-04-09

### Changed
- Redesigned both dark and light themes with radial-gradient backgrounds, glassmorphism card surfaces, and multi-layer shadow system for better visual depth
- Cards now display a color-coded left border matching their source category (GitHub blue, Anthropic gold, OpenAI green, Google red) and emit a matching glow on hover
- Hero title uses a text gradient from the primary text color to the accent color
- Stats bar is now a standalone card with backdrop blur instead of a plain line-separated row
- Theme toggle switch has smoother cubic-bezier animation and a subtle glow in dark mode
- Date group labels include a small accent dot indicator
- Tags gain a border and respond to card hover state
- Footer uses a blurred card-style background to separate it from page content
- Border radii slightly increased (10 → 12 px, 6 → 8 px) for a softer feel

## [0.7.0] - 2026-04-09

### Changed
- Replaced the theme toggle icon button with a sliding toggle switch that uses only CSS shapes, eliminating all SVG and font-glyph rendering issues across Safari, Chrome, and iOS
- Split GitHub relevance matching into separate Product News and Changelog rules so product posts can trust official AI-oriented labels and full article content without making changelog filtering overly broad
- Updated homepage hero subtitle and meta descriptions across Chinese, Japanese, and English to clarify the three-month rolling window and official product update focus

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
