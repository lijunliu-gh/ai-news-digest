# Contributing to AI News Digest

Thanks for your interest in contributing! Here's how you can help.

## Adding News Items

The most common contribution is adding new news items to `data/digest.json`.

### Steps

1. Fork the repository
2. Add your news item(s) to `data/digest.json`
3. Ensure all three languages (zh, ja, en) are provided
4. Submit a Pull Request

### Item Format

```json
{
  "id": "YYYY-MM-DD-NNN",
  "date": "YYYY-MM-DD",
  "category": "microsoft | anthropic | openai | google",
  "title": { "zh": "...", "ja": "...", "en": "..." },
  "summary": { "zh": "...", "ja": "...", "en": "..." },
  "url": "https://official-source-url",
  "tags": ["tag1", "tag2"],
  "source": "Source Name"
}
```

### Guidelines

- **Use official sources only** — Link to the original announcement, not third-party coverage
- **Keep summaries concise** — 1-2 sentences, factual, no opinions
- **Provide all three languages** — zh (Chinese), ja (Japanese), en (English)
- **Use correct categories** — `microsoft` (includes GitHub), `anthropic`, `openai`, `google`
- **Validate JSON** — Run `python3 -c "import json; json.load(open('data/digest.json'))"` before submitting

## Bug Reports & Feature Requests

Open an [Issue](https://github.com/lijunliu-gh/ai-news-digest/issues) with a clear description.

## Code Changes

- Keep it simple — no build tools or frameworks
- Test in both dark and light modes
- Test all three languages
- Ensure responsive design works on mobile

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
