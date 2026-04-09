# Contributing to AI News Digest

Thanks for your interest in contributing! Here's how you can help.

## Adding News Items

The most common contribution is improving the fetcher, UI, or documentation. Direct manual edits to `data/digest.json` are possible, but most active items are now machine-refreshed.

### Steps

1. Fork the repository
2. Add your news item(s) to `data/digest.json`
3. Ensure all three languages (`zh`, `ja`, `en`) are provided, plus a correct `sourceType`
4. Submit a Pull Request

### Item Format

```json
{
  "id": "YYYY-MM-DD-NNN",
  "date": "YYYY-MM-DD",
  "category": "github | anthropic | openai | google",
  "title": { "zh": "...", "ja": "...", "en": "..." },
  "summary": { "zh": "...", "ja": "...", "en": "..." },
  "url": "https://official-source-url",
  "tags": ["tag1", "tag2"],
  "source": "Source Name",
  "sourceType": "news | changelog | release-notes"
}
```

### Guidelines

- **Use official sources only** — Link to the original announcement, not third-party coverage
- **Keep summaries concise** — 1-2 sentences, factual, no opinions
- **Provide all three languages** — zh (Chinese), ja (Japanese), en (English)
- **Use the correct source type** — `news`, `changelog`, or `release-notes`
- **Use correct categories** — `github`, `anthropic`, `openai`, `google`
- **Validate JSON** — Run `python3 -c "import json; json.load(open('data/digest.json'))"` before submitting
- **Do not hand-edit the translation cache unless necessary** — `data/translation-cache.json` is generated and reused by the refresh script

## Bug Reports & Feature Requests

Open an [Issue](https://github.com/lijunliu-gh/ai-news-digest/issues) with a clear description.

## Code Changes

- Keep it simple — no build tools or frameworks
- Install script dependencies with `python3 -m pip install -r requirements.txt` before working on the refresh pipeline
- Test in both dark and light modes
- Test all three languages
- Ensure responsive design works on mobile

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
