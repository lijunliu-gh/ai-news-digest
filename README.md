# AI News Digest

> Official AI product updates from the past three months across **GitHub**, **Anthropic**, **OpenAI**, and **Google**.

🌐 **Live Site:** [https://lijunliu-gh.github.io/ai-news-digest/](https://lijunliu-gh.github.io/ai-news-digest/)

![GitHub Pages](https://img.shields.io/badge/deploy-GitHub%20Pages-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub last commit](https://img.shields.io/github/last-commit/lijunliu-gh/ai-news-digest)
![GitHub release](https://img.shields.io/github/v/release/lijunliu-gh/ai-news-digest)
![GitHub Actions](https://img.shields.io/github/actions/workflow/status/lijunliu-gh/ai-news-digest/update-digest.yml?label=digest%20refresh)

## Features

- 📈 **Trend Chart** — Interactive line chart showing monthly update frequency per company, color-coded and auto-generated from live data
- 🗞️ **Official Release Surfaces** — Aggregates both marketing news and developer-facing changelogs / release notes from Anthropic, OpenAI, Google, and GitHub
- 🌍 **Trilingual** — Switch between 中文 / 日本語 / English with data-level localization for every item
- 🌓 **Dark & Light Mode** — Polished dual themes with gradient backgrounds, glassmorphism cards, category-colored borders, and a sliding toggle switch
- 🔍 **Search & Filter** — Filter by company, source type (News / Changelog / Release Notes), month, and full-text search across titles, summaries, and tags
- ⬆️ **Back to Top & Month Navigator** — Floating back-to-top button and a sidebar month indicator for quick navigation through long feeds
- ♻️ **Automated Refresh** — GitHub Actions refreshes the digest five times a day using only free GitHub-native automation
- 🗄️ **Rolling Window + Archive** — The homepage keeps only the latest 3 months while older items move to an archive dataset
- 📱 **Responsive** — Works on desktop, tablet, and mobile (iOS & Android)
- ⚡ **No Frontend Build Step** — Pure HTML / CSS / JS frontend, with a small Python dependency only for the refresh script

## Project Structure

```
ai-news-digest/
├── index.html          # Main page
├── css/
│   └── style.css       # Styles (dark/light theme, responsive)
├── js/
│   └── app.js          # App logic (i18n, filtering, rendering)
├── data/
│   ├── archive.json    # Older items moved out of the active 3-month window
│   ├── digest.json     # Active news data for the latest 3 months
│   └── translation-cache.json # Cached machine translations for titles and summaries
├── scripts/
│   └── update_digest.py # Official-source fetcher and retention manager
├── .github/
│   └── workflows/
│       └── update-digest.yml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt
└── README.md
```

## Data Sources

| Source | URL |
|--------|-----|
| Anthropic News | https://www.anthropic.com/sitemap.xml + article pages |
| Anthropic Release Notes | https://platform.claude.com/docs/en/release-notes |
| OpenAI News | https://openai.com/news/rss.xml |
| OpenAI API Changelog | https://developers.openai.com/api/docs/changelog |
| Google Blog | https://blog.google/innovation-and-ai/technology/ai/rss/ |
| Google DeepMind News | https://deepmind.google/blog/rss.xml |
| Google Cloud Release Notes | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes |
| GitHub Product News | https://github.blog/news-insights/product-news/ |
| GitHub Changelog | https://github.blog/changelog/feed/ |

## Adding News

Edit `data/digest.json`. Each item follows this structure:

```json
{
  "id": "2026-04-08-001",
  "date": "2026-04-08",
  "category": "anthropic",
  "title": {
    "zh": "中文标题",
    "ja": "日本語タイトル",
    "en": "English Title"
  },
  "summary": {
    "zh": "中文摘要",
    "ja": "日本語の要約",
    "en": "English summary"
  },
  "url": "https://...",
  "tags": ["tag1", "tag2"],
  "source": "Anthropic News",
  "sourceType": "news"
}
```

**Categories:** `github`, `anthropic`, `openai`, `google`

**Source types:** `news`, `changelog`, `release-notes`

## Automation

This repository uses a scheduled GitHub Actions workflow to keep the site current.

- Workflow: `.github/workflows/update-digest.yml`
- Script: `scripts/update_digest.py`
- Active window: latest 3 calendar months
- Archive target: `data/archive.json`

Scheduled refreshes run five times a day, evenly spaced ~4 h 48 min apart:

| UTC | CST (UTC+8) | JST (UTC+9) | PT (UTC−7) |
|-------|-------------|-------------|------------|
| 00:17 | 08:17 | 09:17 | 17:17 (−1) |
| 05:05 | 13:05 | 14:05 | 22:05 (−1) |
| 09:53 | 17:53 | 18:53 | 02:53 |
| 14:41 | 22:41 | 23:41 | 07:41 |
| 19:29 | 03:29 (+1) | 04:29 (+1) | 12:29 |

GitHub Actions uses UTC internally; the workflow cron entries match the UTC column.

### Update Rules

- Only official product-oriented sources are ingested.
- Official sources include both public news pages and developer release-note / changelog surfaces.
- For Anthropic, the scraper discovers articles via the sitemap.xml and extracts published dates and metadata from each article page, giving full coverage beyond the front-page listing.
- For Google, the digest combines Google Blog, Google Cloud release notes, and Google DeepMind product-news posts (via RSS). Keyword filters match product names (Gemini, Gemma, NotebookLM, AI Studio, etc.) while excluding non-product research and safety content.
- For GitHub, Product News and Changelog entries use separate relevance rules: product posts trust official AI-oriented category labels and full article content, while changelog entries apply stricter keyword matching to avoid platform-maintenance noise.
- Locale fields that still match the English source text are treated as untranslated and regenerated during refreshes.
- The homepage dataset is rebuilt from scratch on every run.
- Automated refreshes fail closed when the rebuilt dataset drops below health thresholds or a required official source disappears.
- Health thresholds are configurable through GitHub Actions environment inputs for manual runs and workflow defaults for scheduled runs.
- Manual GitHub Actions runs can override validation thresholds from the workflow dispatch form without editing the script.
- Items older than 3 months are removed from `data/digest.json`.
- Removed items are preserved in `data/archive.json`.
- Existing manual translations are preserved when the same URL already exists.
- Newly fetched English items are machine-translated into Chinese and Japanese, then cached for reuse in later refreshes.
- The translation cache lives in `data/translation-cache.json` and is committed so future runs reuse the same phrasing.
- The homepage shows whether an item came from a news page, changelog, or release-notes surface.
- Each GitHub Actions run publishes a job summary with total items, per-source counts, translation stats, validation config, and any validation issues.

## Development

No frontend build tools are needed. For the automation script, install Python dependencies first:

```bash
python3 -m pip install -r requirements.txt
```

Then open `index.html` in a browser, run a local server, or rebuild the datasets manually:

```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve .

# Refresh digest data
python3 scripts/update_digest.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)

---

Curated by [RoundTable AI Lab](https://roundtableailab.org)
