# AI News Digest

> Daily curated AI news from **Microsoft / GitHub**, **Anthropic**, **OpenAI**, and **Google**.

🌐 **Live Site:** [https://lijunliu-gh.github.io/ai-news-digest/](https://lijunliu-gh.github.io/ai-news-digest/)

![GitHub Pages](https://img.shields.io/badge/deploy-GitHub%20Pages-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🗞️ **Four AI Sources** — Aggregates news from [Anthropic](https://www.anthropic.com/news), [OpenAI](https://openai.com/news/), [Google Gemini](https://blog.google/products-and-platforms/products/gemini/), and [GitHub](https://github.blog/news-insights/product-news/)
- 🌍 **Trilingual** — Switch between 中文 / 日本語 / English
- 🌓 **Dark & Light Mode** — Respects user preference with manual toggle
- 🔍 **Search & Filter** — Filter by company, search across titles, summaries, and tags
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
│   └── digest.json     # News data (trilingual)
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
