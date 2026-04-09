# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
