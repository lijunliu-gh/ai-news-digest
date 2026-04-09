# AI News Digest

> Daily curated AI news from **Microsoft / GitHub**, **Anthropic**, **OpenAI**, and **Google**.

🌐 **Live Site:** [https://lijunliu-gh.github.io/ai-news-digest/](https://lijunliu-gh.github.io/ai-news-digest/)

![GitHub Pages](https://img.shields.io/badge/deploy-GitHub%20Pages-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🗞️ **Four AI Sources** — Aggregates news from [Anthropic](https://www.anthropic.com/news), [OpenAI](https://openai.com/news/), [Google Gemini](https://blog.google/products-and-platforms/products/gemini/), and [GitHub](https://github.blog/news-insights/product-news/)
- 🌍 **Trilingual** — Switch between 中文 / 日本語 / English
- 🌓 **Dark & Light Mode** — Respects user preference with manual toggle
- 🔍 **Search & Filter** — Filter by company, month, and search across titles, summaries, and tags
- ♻️ **Automated Refresh** — GitHub Actions refreshes the digest five times a day using only free GitHub-native automation
- 🗄️ **Rolling Window + Archive** — The homepage keeps only the latest 3 months while older items move to an archive dataset
- 📱 **Responsive** — Works on desktop, tablet, and mobile
- ⚡ **Zero Dependencies** — Pure HTML / CSS / JS, no build step required

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
│   └── digest.json     # Active news data for the latest 3 months
├── scripts/
│   └── update_digest.py # Official-source fetcher and retention manager
├── .github/
│   └── workflows/
│       └── update-digest.yml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Data Sources

| Source | URL |
|--------|-----|
| Anthropic | https://www.anthropic.com/news |
| OpenAI | https://openai.com/news/company-announcements/ |
| Google Gemini | https://blog.google/products-and-platforms/products/gemini/ |
| GitHub / Microsoft | https://github.blog/news-insights/product-news/ |

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
  "source": "Anthropic News"
}
```

**Categories:** `microsoft`, `anthropic`, `openai`, `google`

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
- The homepage dataset is rebuilt from scratch on every run.
- Items older than 3 months are removed from `data/digest.json`.
- Removed items are preserved in `data/archive.json`.
- Existing manual translations are preserved when the same URL already exists.
- Newly fetched items default to English text in all three language fields unless translations already exist locally.

## Development

No build tools needed. Just open `index.html` in a browser, or run a local server:

```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)

---

Curated by [RoundTable AI Lab](https://roundtableailab.org)
