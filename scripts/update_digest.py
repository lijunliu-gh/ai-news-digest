from __future__ import annotations

import json
import os
import re
import sys
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DIGEST_PATH = DATA_DIR / 'digest.json'
ARCHIVE_PATH = DATA_DIR / 'archive.json'
WINDOW_MONTHS = 3
REQUEST_TIMEOUT = 30
USER_AGENT = 'ai-news-digest-bot/0.4'


@dataclass
class FeedEntry:
    date: str
    category: str
    source: str
    title_en: str
    summary_en: str
    url: str
    tags: list[str]


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {'script', 'style'}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {'script', 'style'} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)

    def text(self) -> str:
        return normalize_whitespace(' '.join(self.parts))


def normalize_whitespace(text: str) -> str:
    return ' '.join(unescape(text).replace('\xa0', ' ').split())


def strip_html(html_text: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()
    return parser.text()


def fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8',
        },
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read().decode('utf-8', errors='replace')


def try_fetch_text(url: str) -> str | None:
    try:
        return fetch_text(url)
    except (HTTPError, URLError):
        return None


def subtract_months(day: date, months: int) -> date:
    year = day.year
    month = day.month - months
    while month <= 0:
        month += 12
        year -= 1
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def get_today() -> date:
    override = None
    if len(sys.argv) > 1:
        override = sys.argv[1]
    if override:
        return date.fromisoformat(override)
    env_override = os.environ.get('TODAY_OVERRIDE')
    return date.fromisoformat(env_override) if env_override else date.today()


def within_window(day_str: str, cutoff: date) -> bool:
    return date.fromisoformat(day_str) >= cutoff


def parse_rss(url: str) -> list[ET.Element]:
    root = ET.fromstring(fetch_text(url))
    channel = root.find('channel')
    return [] if channel is None else channel.findall('item')


def first_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return normalize_whitespace(child.text or '') if child is not None and child.text else ''


def parse_pub_date(value: str) -> str:
    return parsedate_to_datetime(value).date().isoformat()


def normalize_tag(value: str) -> str:
    cleaned = normalize_whitespace(value).lower()
    cleaned = re.sub(r'[^a-z0-9]+', '-', cleaned).strip('-')
    return cleaned


def unique_tags(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        tag = normalize_tag(value)
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


def clean_description(value: str) -> str:
    text = strip_html(value)
    text = re.sub(r'\s*The post .*? appeared first on The GitHub Blog\.?$', '', text, flags=re.I)
    return normalize_whitespace(text)


def extract_meta_description(html: str) -> str:
    for pattern in (
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    ):
        match = re.search(pattern, html, flags=re.I)
        if match:
            return normalize_whitespace(match.group(1))
    return ''


def load_existing_items() -> tuple[dict[str, dict], list[dict]]:
    existing_by_url: dict[str, dict] = {}
    archived_items: list[dict] = []
    for path in (ARCHIVE_PATH, DIGEST_PATH):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        items = payload.get('items', [])
        if path == ARCHIVE_PATH:
            archived_items.extend(items)
        for item in items:
            existing_by_url.setdefault(item.get('url', ''), item)
    return existing_by_url, archived_items


def localize(existing: dict | None, field: str, english_text: str) -> dict[str, str]:
    value = existing.get(field) if existing else None
    if isinstance(value, dict):
        return {
            'zh': value.get('zh') or value.get('en') or english_text,
            'ja': value.get('ja') or value.get('en') or english_text,
            'en': value.get('en') or english_text,
        }
    if isinstance(value, str) and value:
        return {'zh': value, 'ja': value, 'en': value}
    return {'zh': english_text, 'ja': english_text, 'en': english_text}


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip('/')
    slug = path.split('/')[-1] if path else 'item'
    slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
    return slug or 'item'


def materialize(entries: list[FeedEntry], existing_by_url: dict[str, dict]) -> list[dict]:
    items: list[dict] = []
    used_ids: set[str] = set()
    seen_urls: set[str] = set()

    for entry in sorted(entries, key=lambda item: (item.date, item.url), reverse=True):
        if entry.url in seen_urls:
            continue
        seen_urls.add(entry.url)
        existing = existing_by_url.get(entry.url)
        item_id = f"{entry.date}-{entry.category}-{slug_from_url(entry.url)}"
        suffix = 2
        while item_id in used_ids:
            item_id = f"{entry.date}-{entry.category}-{slug_from_url(entry.url)}-{suffix}"
            suffix += 1
        used_ids.add(item_id)

        items.append({
            'id': item_id,
            'date': entry.date,
            'category': entry.category,
            'title': localize(existing, 'title', entry.title_en),
            'summary': localize(existing, 'summary', entry.summary_en),
            'url': entry.url,
            'tags': entry.tags,
            'source': entry.source,
        })

    return items


def parse_openai_entries(cutoff: date) -> list[FeedEntry]:
    allowed_categories = {
        'Company',
        'Product',
        'Safety',
        'Safety & Alignment',
        'Security',
        'Global Affairs',
        'Research',
        'Engineering',
        'Publication',
        'API',
        'Release',
        'NONE',
    }
    entries: list[FeedEntry] = []
    for item in parse_rss('https://openai.com/news/rss.xml'):
        published = parse_pub_date(first_text(item, 'pubDate'))
        if not within_window(published, cutoff):
            continue
        title = first_text(item, 'title')
        description = clean_description(first_text(item, 'description'))
        link = first_text(item, 'link')
        categories = [normalize_whitespace(node.text or '') for node in item.findall('category') if node.text]
        primary_category = categories[0] if categories else 'NONE'
        if primary_category not in allowed_categories:
            continue
        entries.append(FeedEntry(
            date=published,
            category='openai',
            source='OpenAI News',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['openai']),
        ))
    return entries


def is_google_relevant(title: str, summary: str, url: str, categories: list[str]) -> bool:
    haystack = ' '.join([title, summary, url, *categories]).lower()
    return any(token in haystack for token in ('gemini', 'gemma', 'google-ai-updates', 'ai updates'))


def parse_google_entries(cutoff: date) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for item in parse_rss('https://blog.google/innovation-and-ai/technology/ai/rss/'):
        published = parse_pub_date(first_text(item, 'pubDate'))
        if not within_window(published, cutoff):
            continue
        title = first_text(item, 'title')
        description = clean_description(first_text(item, 'description'))
        link = first_text(item, 'link') or first_text(item, 'guid')
        categories = [normalize_whitespace(node.text or '') for node in item.findall('category') if node.text]
        if not is_google_relevant(title, description, link, categories):
            continue
        entries.append(FeedEntry(
            date=published,
            category='google',
            source='Google Blog',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['google']),
        ))
    return entries


def is_github_relevant(title: str, summary: str, url: str, categories: list[str]) -> bool:
    haystack = ' '.join([title, summary, url, *categories]).lower()
    return any(token in haystack for token in ('copilot', 'agent', 'ai', 'actions', 'model'))


def parse_github_entries(cutoff: date) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for item in parse_rss('https://github.blog/news-insights/product-news/feed/'):
        published = parse_pub_date(first_text(item, 'pubDate'))
        if not within_window(published, cutoff):
            continue
        title = first_text(item, 'title')
        description = clean_description(first_text(item, 'description'))
        link = first_text(item, 'link')
        categories = [normalize_whitespace(node.text or '') for node in item.findall('category') if node.text]
        if not is_github_relevant(title, description, link, categories):
            continue
        entries.append(FeedEntry(
            date=published,
            category='microsoft',
            source='GitHub Product News',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['github']),
        ))
    return entries


def resolve_anthropic_url(slug: str) -> tuple[str, str]:
    for candidate in (f'https://www.anthropic.com/news/{slug}', f'https://www.anthropic.com/{slug}'):
        html = try_fetch_text(candidate)
        if html:
            return candidate, html
    return f'https://www.anthropic.com/news/{slug}', ''


def parse_anthropic_entries(cutoff: date) -> list[FeedEntry]:
    html = fetch_text('https://www.anthropic.com/news')
    entries: list[FeedEntry] = []
    seen_urls: set[str] = set()

    featured_pattern = re.compile(
        r'<a href="(?P<href>/[^"]+)" class="FeaturedGrid-module-scss-module__[^"]+__content">'
        r'<h2[^>]*>(?P<title>[^<]+)</h2>.*?'
        r'<span class="caption bold">(?P<subject>[^<]+)</span>'
        r'<time[^>]*>(?P<published>[^<]+)</time>.*?'
        r'<p[^>]*>(?P<summary>.*?)</p>',
        re.S,
    )
    list_pattern = re.compile(
        r'<li><a href="(?P<href>/news/[^"]+)" class="PublicationList-module-scss-module__[^"]+__listItem">.*?'
        r'<time[^>]*>(?P<published>[^<]+)</time>'
        r'<span[^>]*>(?P<subject>[^<]+)</span>.*?'
        r'<span class="PublicationList-module-scss-module__[^"]+__title body-3">(?P<title>[^<]+)</span>',
        re.S,
    )

    def add_match(href: str, title: str, published_label: str, subject: str, summary: str | None) -> None:
        published = datetime.strptime(normalize_whitespace(published_label), '%b %d, %Y').date().isoformat()
        if not within_window(published, cutoff):
            return
        article_url = f'https://www.anthropic.com{href}'
        if article_url in seen_urls:
            return
        seen_urls.add(article_url)

        article_html = try_fetch_text(article_url) or ''
        meta_summary = extract_meta_description(article_html)
        final_summary = normalize_whitespace((summary or '').strip()) or meta_summary or normalize_whitespace(title)
        entries.append(FeedEntry(
            date=published,
            category='anthropic',
            source='Anthropic News',
            title_en=normalize_whitespace(title),
            summary_en=final_summary,
            url=article_url,
            tags=unique_tags([subject, 'anthropic']),
        ))

    for match in featured_pattern.finditer(html):
        add_match(
            match.group('href'),
            strip_html(match.group('title')),
            match.group('published'),
            match.group('subject'),
            strip_html(match.group('summary')),
        )

    for match in list_pattern.finditer(html):
        add_match(
            match.group('href'),
            strip_html(match.group('title')),
            match.group('published'),
            strip_html(match.group('subject')),
            None,
        )

    return entries


def merge_archive(existing_archive: list[dict], previous_digest: list[dict], fresh_digest: list[dict], cutoff: date) -> list[dict]:
    archive_by_url: dict[str, dict] = {}
    for item in existing_archive + previous_digest:
        url = item.get('url')
        if not url:
            continue
        if date.fromisoformat(item['date']) >= cutoff:
            continue
        archive_by_url.setdefault(url, item)

    for item in fresh_digest:
        if date.fromisoformat(item['date']) < cutoff:
            archive_by_url.setdefault(item['url'], item)

    return sorted(archive_by_url.values(), key=lambda item: (item['date'], item['id']), reverse=True)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    today = get_today()
    cutoff = subtract_months(today, WINDOW_MONTHS)

    existing_by_url, existing_archive = load_existing_items()
    previous_digest = []
    if DIGEST_PATH.exists():
        previous_digest = json.loads(DIGEST_PATH.read_text(encoding='utf-8')).get('items', [])

    fresh_entries = (
        parse_anthropic_entries(cutoff)
        + parse_openai_entries(cutoff)
        + parse_google_entries(cutoff)
        + parse_github_entries(cutoff)
    )
    fresh_digest = materialize(fresh_entries, existing_by_url)
    fresh_digest = [item for item in fresh_digest if date.fromisoformat(item['date']) >= cutoff]
    fresh_digest.sort(key=lambda item: (item['date'], item['id']), reverse=True)

    archive_items = merge_archive(existing_archive, previous_digest, fresh_digest, cutoff)

    write_json(DIGEST_PATH, {
        'lastUpdated': today.isoformat(),
        'windowMonths': WINDOW_MONTHS,
        'items': fresh_digest,
    })
    write_json(ARCHIVE_PATH, {
        'lastUpdated': today.isoformat(),
        'windowMonths': WINDOW_MONTHS,
        'items': archive_items,
    })

    print(f'Updated digest with {len(fresh_digest)} active items and {len(archive_items)} archived items.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())