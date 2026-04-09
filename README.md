# AI News Digest

> Daily curated AI news from **Microsoft / GitHub**, **Anthropic**, **OpenAI**, and **Google**.

🌐 **Live Site:** [https://lijunliu-gh.github.io/ai-news-digest/](https://lijunliu-gh.github.io/ai-news-digest/)

![GitHub Pages](https://img.shields.io/badge/deploy-GitHub%20Pages-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🗞️ **Official Release Surfaces** — Aggregates both marketing news and developer-facing changelogs / release notes from Anthropic, OpenAI, Google, and GitHub
- 🌍 **Trilingual** — Switch between 中文 / 日本語 / English with data-level localization for every item
- 🌓 **Dark & Light Mode** — Respects user preference with manual toggle
- 🎛️ **Clear Theme Toggle** — The header theme switch now shows both an icon and a text label instead of an ambiguous icon-only button
- 🔍 **Search & Filter** — Filter by company, month, and search across titles, summaries, tags, and official source surfaces
- ♻️ **Automated Refresh** — GitHub Actions refreshes the digest five times a day using only free GitHub-native automation
- 🗄️ **Rolling Window + Archive** — The homepage keeps only the latest 3 months while older items move to an archive dataset
- 📱 **Responsive** — Works on desktop, tablet, and mobile
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
| Anthropic News | https://www.anthropic.com/news |
| Anthropic Release Notes | https://platform.claude.com/docs/en/release-notes |
| OpenAI News | https://openai.com/news/rss.xml |
| OpenAI API Changelog | https://developers.openai.com/api/docs/changelog |
| Google Blog | https://blog.google/innovation-and-ai/technology/ai/rss/ |
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

**Categories:** `microsoft`, `anthropic`, `openai`, `google`

**Source types:** `news`, `changelog`, `release-notes`

## Automation

This repository uses a scheduled GitHub Actions workflow to keep the site current.

- Workflow: `.github/workflows/update-digest.yml`
- Script: `scripts/update_digest.py`
- Active window: latest 3 calendar months
- Archive target: `data/archive.json`

Scheduled refreshes run at these China Standard Time slots by default:

- 07:12
- 11:21
- 15:12
- 19:21
- 23:12

GitHub Actions uses UTC internally, so the workflow cron is stored as UTC equivalents.

### Update Rules

- Only official sources are ingested.
- Official sources include both public news pages and developer release-note / changelog surfaces.
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
