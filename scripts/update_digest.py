from __future__ import annotations

import json
import os
import re
import sys
from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DIGEST_PATH = DATA_DIR / 'digest.json'
ARCHIVE_PATH = DATA_DIR / 'archive.json'
TRANSLATION_CACHE_PATH = DATA_DIR / 'translation-cache.json'
REPORT_PATH = ROOT / '.digest-report.json'
WINDOW_MONTHS = 3
REQUEST_TIMEOUT = 30
USER_AGENT = 'ai-news-digest-bot/0.5'
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
TRANSLATION_TARGETS = ('zh', 'ja')
TRANSLATION_LANGUAGE_CODES = {
    'zh': 'zh-CN',
    'ja': 'ja',
}
DEFAULT_MIN_ACTIVE_ITEMS = 60
DEFAULT_TOTAL_DROP_RATIO = 0.6
DEFAULT_SOURCE_DROP_RATIO = 0.4
DEFAULT_SOURCE_BASELINE = 3
DEFAULT_OPTIONAL_SOURCES = {'GitHub Product News'}
DEFAULT_REQUIRED_SOURCES = {
    'Anthropic News',
    'Anthropic Release Notes',
    'OpenAI News',
    'OpenAI API Changelog',
    'Google Blog',
    'Google Cloud Release Notes',
    'GitHub Changelog',
}


@dataclass
class FeedEntry:
    date: str
    category: str
    source: str
    source_type: str
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
    cleaned = ' '.join(unescape(text).replace('\xa0', ' ').split())
    return re.sub(r'\s+([,.;:!?])', r'\1', cleaned)


def slugify_text(value: str) -> str:
    return normalize_tag(value)


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


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name, '').strip()
    if not value:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name, '').strip()
    if not value:
        return default
    return float(value)


def env_csv_set(name: str, default: set[str]) -> set[str]:
    value = os.environ.get(name, '').strip()
    if not value:
        return set(default)
    return {normalize_whitespace(part) for part in value.split(',') if normalize_whitespace(part)}


def get_validation_config() -> dict[str, int | float | set[str]]:
    return {
        'min_active_items': env_int('DIGEST_MIN_ACTIVE_ITEMS', DEFAULT_MIN_ACTIVE_ITEMS),
        'total_drop_ratio': env_float('DIGEST_TOTAL_DROP_RATIO', DEFAULT_TOTAL_DROP_RATIO),
        'source_drop_ratio': env_float('DIGEST_SOURCE_DROP_RATIO', DEFAULT_SOURCE_DROP_RATIO),
        'source_baseline': env_int('DIGEST_SOURCE_BASELINE', DEFAULT_SOURCE_BASELINE),
        'required_sources': env_csv_set('DIGEST_REQUIRED_SOURCES', DEFAULT_REQUIRED_SOURCES),
        'optional_sources': env_csv_set('DIGEST_OPTIONAL_SOURCES', DEFAULT_OPTIONAL_SOURCES),
    }


def within_window(day_str: str, cutoff: date) -> bool:
    return date.fromisoformat(day_str) >= cutoff


def parse_rss(url: str) -> list[ET.Element]:
    root = ET.fromstring(fetch_text(url))
    channel = root.find('channel')
    return [] if channel is None else channel.findall('item')


def parse_atom(url: str) -> list[ET.Element]:
    root = ET.fromstring(fetch_text(url))
    return root.findall('atom:entry', ATOM_NS)


def first_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return normalize_whitespace(child.text or '') if child is not None and child.text else ''


def parse_pub_date(value: str) -> str:
    value = normalize_whitespace(value)
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
    except ValueError:
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
    text = re.sub(r'\bThe post\b.*?\bappeared first on The GitHub Blog\b\s*\.?', '', text, flags=re.I)
    return normalize_whitespace(text)


def append_anchor(url: str, anchor_suffix: str) -> str:
    clean_suffix = slugify_text(anchor_suffix) or 'item'
    if '#' in url:
        base, fragment = url.split('#', 1)
        return f'{base}#{fragment}-{clean_suffix}'
    return f'{url}#{clean_suffix}'


def first_sentence(text: str) -> str:
    text = normalize_whitespace(text)
    if not text:
        return ''
    match = re.match(r'(.+?[.!?])(?:\s|$)', text)
    sentence = match.group(1) if match else text
    sentence = sentence.strip()
    if len(sentence) <= 120:
        return sentence
    words = sentence.split()
    return ' '.join(words[:12]).rstrip('.,;:')


def extract_link_texts(html: str) -> list[str]:
    return [normalize_whitespace(strip_html(match)) for match in re.findall(r'<a[^>]*>(.*?)</a>', html, re.I | re.S)]


def extract_emphasized_text(html: str) -> str:
    for pattern in (r'<strong[^>]*>(.*?)</strong>', r'<code[^>]*>(.*?)</code>'):
        match = re.search(pattern, html, re.I | re.S)
        if match:
            text = normalize_whitespace(strip_html(match.group(1)))
            if text:
                return text
    return ''


def is_valid_release_title(candidate: str) -> bool:
    normalized = normalize_whitespace(strip_html(candidate))
    lowered = normalized.lower()
    if not normalized:
        return False
    if normalized.startswith('/'):
        return False
    if lowered.startswith('we ') or lowered.startswith("we've "):
        return False
    if lowered.startswith('learn more '):
        return False
    if lowered in {'here', 'learn more', 'read more', 'more', 'details'}:
        return False
    return len(normalized) <= 96


def derive_release_title(text: str) -> str:
    normalized = normalize_whitespace(text)
    patterns: list[tuple[str, callable]] = [
        (r"^(?:We've launched|We launched|Launching|Introduced|Introducing|Added|Released)\s+(?:the\s+)?(.+?)(?:,|\.|\s+for\b|\s+in\b|\s+as\b|\s+that\b)", lambda m: m.group(1)),
        (r'^The\s+(.+?)\s+is now available on\s+(.+?)(?:\s+as\b|,|\.|$)', lambda m: f'{m.group(1)} on {m.group(2)}'),
        (r'^The\s+(.+?)\s+is now available(?:\s+as\b|,|\.|$)', lambda m: m.group(1)),
        (r'^We announced\s+(.+?)\s+is available(?:\s+as\b|,|\.|$)', lambda m: m.group(1)),
        (r'^(.+?)\s+is now available(?:\s+as\b|,|\.|$)', lambda m: m.group(1)),
    ]
    for pattern, formatter in patterns:
        match = re.search(pattern, normalized, re.I)
        if not match:
            continue
        candidate = normalize_whitespace(formatter(match))
        if is_valid_release_title(candidate):
            return candidate
    return ''


def choose_release_title(text: str, *candidates: str) -> str:
    for candidate in candidates:
        candidate = normalize_whitespace(candidate)
        if is_valid_release_title(candidate):
            return candidate
    derived = derive_release_title(text)
    if derived:
        return derived
    return first_sentence(text) or 'Update'


def parse_section_date(month_name: str, year: str, day_label: str) -> str:
    day_number = re.search(r'(\d{1,2})', day_label)
    if not day_number:
        raise ValueError(f'Unrecognized day label: {day_label}')
    return datetime.strptime(f'{month_name} {day_number.group(1)} {year}', '%B %d %Y').date().isoformat()


def is_openai_changelog_relevant(kind: str, badges: list[str], body_text: str) -> bool:
    text = ' '.join([kind, *badges, body_text]).lower()
    strong_signal = (
        'gpt-', 'responses', 'chat completions', 'chatgpt', 'realtime', 'audio', 'image',
        'video', 'sora', 'codex', 'tool', 'skills', 'shell', 'computer use', 'compaction',
        'reasoning', 'websocket', 'webhook', 'connector', 'agent', 'fine-tuning',
        'batch api', 'assistants', 'evals', 'embedding', 'vision'
    )
    low_signal = (
        'slug to point to the latest model',
        'latest model currently used in chatgpt',
        'points to the',
        'point to the',
        'slugs to point to',
        'snapshot',
        'snapshots',
        'rate limits page',
        'documentation update',
        'docs update',
        'typo fix',
        'clarified documentation',
        'renamed a field',
        'intermediate commentary',
    )
    kind_lower = kind.lower()
    if any(token in text for token in low_signal):
        return False
    if kind_lower in {'feature', 'announcement', 'deprecated'}:
        return any(token in text for token in strong_signal)
    if kind_lower == 'update':
        return any(token in text for token in strong_signal) and any(token in text for token in (
            'gpt-', 'responses', 'realtime', 'audio', 'image', 'video', 'codex', 'tool',
            'agent', 'fine-tuning', 'embedding', 'vision', 'webhook', 'connector'
        ))
    return False


def is_google_release_relevant(title: str, summary: str, kind: str) -> bool:
    text = ' '.join([title, summary, kind]).lower()
    if any(token in text for token in (
        'anthropic', 'deepseek', 'mistral', 'qwen', 'glm ', 'codestral', 'llama',
        'phi-', 'kimi', 'minimax', 'whisper', 'openai', 'claude '
    )):
        return False
    return any(token in text for token in (
        'gemini', 'gemma', 'veo', 'imagen', 'lyria', 'vertex ai agent engine', 'agent engine',
        'agent development kit', 'adk', 'agent garden', 'live api', 'grounding',
        'prompt optimizer', 'rag engine', 'vertex ai studio', 'google gen ai sdk'
    ))


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


def load_translation_cache() -> dict[str, dict[str, str]]:
    if not TRANSLATION_CACHE_PATH.exists():
        return {}
    payload = json.loads(TRANSLATION_CACHE_PATH.read_text(encoding='utf-8'))
    return payload if isinstance(payload, dict) else {}


class TranslationService:
    def __init__(self, cache: dict[str, dict[str, str]]) -> None:
        self.enabled = os.environ.get('DIGEST_ENABLE_TRANSLATION', '1') != '0'
        self.cache = cache
        self.clients: dict[str, object] = {}
        self.dirty = False
        self.cache_hits = 0
        self.generated = 0
        self.errors: list[str] = []

    def translate(self, text: str, target: str) -> str:
        normalized = normalize_whitespace(text)
        if not normalized or target == 'en' or not self.enabled:
            return normalized

        cached = self.cache.get(normalized, {})
        cached_value = normalize_whitespace(cached.get(target, '')) if isinstance(cached, dict) else ''
        if cached_value:
            self.cache_hits += 1
            return cached_value

        if GoogleTranslator is None:
            self._record_error('Translation package missing; falling back to English text.')
            return normalized

        try:
            client = self.clients.get(target)
            if client is None:
                client = GoogleTranslator(source='en', target=TRANSLATION_LANGUAGE_CODES.get(target, target))
                self.clients[target] = client
            translated = normalize_whitespace(client.translate(normalized))
            if not translated:
                translated = normalized
            self.cache.setdefault(normalized, {})[target] = translated
            self.generated += 1
            self.dirty = True
            return translated
        except Exception as exc:
            self._record_error(f'Translation failed for {target}: {exc}')
            return normalized

    def stats(self) -> dict[str, object]:
        return {
            'enabled': self.enabled,
            'cacheEntries': len(self.cache),
            'cacheHits': self.cache_hits,
            'generated': self.generated,
            'errors': self.errors[:10],
        }

    def _record_error(self, message: str) -> None:
        if message not in self.errors:
            self.errors.append(message)


def save_translation_cache(cache: dict[str, dict[str, str]]) -> None:
    write_json(TRANSLATION_CACHE_PATH, cache)


def is_generated_localization(value: dict | str | None) -> bool:
    if isinstance(value, str):
        return bool(value)
    if not isinstance(value, dict):
        return False
    normalized_values = [normalize_whitespace(value.get(lang, '')) for lang in ('zh', 'ja', 'en') if value.get(lang)]
    return bool(normalized_values) and len(set(normalized_values)) == 1


def localize(
    existing: dict | None,
    field: str,
    english_text: str,
    translator: TranslationService,
    refresh_generated: bool = False,
) -> dict[str, str]:
    value = existing.get(field) if existing else None
    if isinstance(value, dict):
        english_value = value.get('en') or english_text
        if refresh_generated and is_generated_localization(value):
            return {
                'zh': translator.translate(english_text, 'zh'),
                'ja': translator.translate(english_text, 'ja'),
                'en': english_text,
            }
        return {
            'zh': value.get('zh') or translator.translate(english_value, 'zh'),
            'ja': value.get('ja') or translator.translate(english_value, 'ja'),
            'en': english_value,
        }
    if isinstance(value, str) and value:
        if refresh_generated:
            return {
                'zh': translator.translate(english_text, 'zh'),
                'ja': translator.translate(english_text, 'ja'),
                'en': english_text,
            }
        return {
            'zh': translator.translate(value, 'zh'),
            'ja': translator.translate(value, 'ja'),
            'en': value,
        }
    return {
        'zh': translator.translate(english_text, 'zh'),
        'ja': translator.translate(english_text, 'ja'),
        'en': english_text,
    }


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip('/')
    slug = path.split('/')[-1] if path else 'item'
    slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
    return slug or 'item'


def materialize(entries: list[FeedEntry], existing_by_url: dict[str, dict], translator: TranslationService) -> list[dict]:
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
            'title': localize(existing, 'title', entry.title_en, translator, refresh_generated=True),
            'summary': localize(existing, 'summary', entry.summary_en, translator, refresh_generated=True),
            'url': entry.url,
            'tags': entry.tags,
            'source': entry.source,
            'sourceType': entry.source_type,
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
            source_type='news',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['openai']),
        ))
    return entries


def parse_openai_changelog_entries(cutoff: date) -> list[FeedEntry]:
    html = fetch_text('https://developers.openai.com/api/docs/changelog')
    entries: list[FeedEntry] = []
    section_pattern = re.compile(
        r'<h3 class="[^"]*_ChangelogSectionTitle[^"]*">(?P<month>[A-Za-z]+), (?P<year>\d{4})</h3>(?P<section>.*?)(?=<h3 class="[^"]*_ChangelogSectionTitle|<footer|</main>)',
        re.S,
    )
    entry_pattern = re.compile(
        r'<div class="mt-5"><div class="grid[^>]*>.*?<div class="_Badge[^"]*"[^>]*data-variant="outline">(?P<day_label>[A-Za-z]{3} \d{1,2})</div>.*?'
        r'<div class="flex flex-wrap gap-2 mb-2">(?P<badges>.*?)</div><div class="_MarkdownContent[^"]*">(?P<body>.*?)</div></div></div></div>',
        re.S,
    )

    for section_match in section_pattern.finditer(html):
        month_name = section_match.group('month')
        year = section_match.group('year')
        section_html = section_match.group('section')
        for match in entry_pattern.finditer(section_html):
            published = parse_section_date(month_name, year, match.group('day_label'))
            if not within_window(published, cutoff):
                continue
            badge_values = [
                normalize_whitespace(strip_html(value))
                for value in re.findall(r'data-variant="soft">(.*?)</div>', match.group('badges'), re.S)
            ]
            if not badge_values:
                continue
            kind = badge_values[0]
            body_html = match.group('body')
            body_text = normalize_whitespace(strip_html(body_html))
            if not is_openai_changelog_relevant(kind, badge_values[1:], body_text):
                continue

            paragraphs = re.findall(r'<p>(.*?)</p>', body_html, re.S)
            first_paragraph = normalize_whitespace(strip_html(paragraphs[0])) if paragraphs else body_text
            link_texts = [text for text in extract_link_texts(paragraphs[0] if paragraphs else body_html) if text]
            headline_candidates = [text for text in link_texts if '/' not in text and len(text) <= 64]
            title = choose_release_title(first_paragraph, ', '.join(headline_candidates[:2]), first_sentence(first_paragraph))
            summary = body_text
            url = append_anchor('https://developers.openai.com/api/docs/changelog', f'{published}-{kind}-{title}')
            entries.append(FeedEntry(
                date=published,
                category='openai',
                source='OpenAI API Changelog',
                source_type='changelog',
                title_en=title,
                summary_en=summary,
                url=url,
                tags=unique_tags(badge_values[1:] + [kind, 'openai', 'changelog']),
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
            source_type='news',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['google']),
        ))
    return entries


def parse_google_release_entries(cutoff: date) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for entry in parse_atom('https://docs.cloud.google.com/feeds/generative-ai-on-vertex-ai-release-notes.xml'):
        published = parse_pub_date(entry.findtext('atom:updated', default='', namespaces=ATOM_NS))
        if not within_window(published, cutoff):
            continue

        link = ''
        for link_node in entry.findall('atom:link', ATOM_NS):
            if link_node.get('rel') == 'alternate':
                link = link_node.get('href', '')
                break

        content_html = entry.findtext('atom:content', default='', namespaces=ATOM_NS)
        kind_match = re.search(r'<h3>(.*?)</h3>', content_html, re.I | re.S)
        title_match = re.search(r'<strong>(.*?)</strong>', content_html, re.I | re.S)
        kind = normalize_whitespace(strip_html(kind_match.group(1))) if kind_match else 'Update'
        title = normalize_whitespace(strip_html(title_match.group(1))) if title_match else first_sentence(strip_html(content_html))
        summary = normalize_whitespace(strip_html(content_html))
        if not is_google_release_relevant(title, summary, kind):
            continue

        entries.append(FeedEntry(
            date=published,
            category='google',
            source='Google Cloud Release Notes',
            source_type='release-notes',
            title_en=title,
            summary_en=summary,
            url=append_anchor(link, title),
            tags=unique_tags([kind, 'google', 'release-notes']),
        ))
    return entries


def is_github_relevant(title: str, summary: str, url: str, categories: list[str]) -> bool:
    haystack = ' '.join([title, summary, url, *categories]).lower()
    return bool(re.search(r'\bcopilot\b|\bagent\b|\bactions\b|\bmodels?\b|\bai\b', haystack))


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
            source_type='news',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['github']),
        ))
    return entries


def parse_github_changelog_entries(cutoff: date) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for item in parse_rss('https://github.blog/changelog/feed/'):
        published = parse_pub_date(first_text(item, 'pubDate'))
        if not within_window(published, cutoff):
            continue
        title = first_text(item, 'title')
        description = clean_description(first_text(item, 'description'))
        link = first_text(item, 'link') or first_text(item, 'guid')
        categories = [normalize_whitespace(node.text or '') for node in item.findall('category') if node.text]
        if not is_github_relevant(title, description, link, categories):
            continue
        entries.append(FeedEntry(
            date=published,
            category='microsoft',
            source='GitHub Changelog',
            source_type='changelog',
            title_en=title,
            summary_en=description,
            url=link,
            tags=unique_tags(categories + ['github', 'changelog']),
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
            source_type='news',
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


def parse_anthropic_release_entries(cutoff: date) -> list[FeedEntry]:
    html = fetch_text('https://platform.claude.com/docs/en/release-notes')
    entries: list[FeedEntry] = []
    section_pattern = re.compile(
        r'<h3[^>]*><div class="group relative pt-6 pb-2" id="(?P<anchor>[^"]+)">.*?<div>(?P<published>[A-Za-z]+ \d{1,2}, \d{4})</div>.*?</h3>\s*<ul[^>]*>(?P<body>.*?)</ul>',
        re.S,
    )
    item_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.S)

    for section_match in section_pattern.finditer(html):
        published = datetime.strptime(normalize_whitespace(section_match.group('published')), '%B %d, %Y').date().isoformat()
        if not within_window(published, cutoff):
            continue
        base_link = f"https://platform.claude.com/docs/en/release-notes#{section_match.group('anchor')}"
        for item_html in item_pattern.findall(section_match.group('body')):
            summary = normalize_whitespace(strip_html(item_html))
            if not summary:
                continue
            emphasized = extract_emphasized_text(item_html)
            link_texts = [text for text in extract_link_texts(item_html) if text]
            first_link = re.search(r'href="([^"]+)"', item_html)
            link = urljoin('https://platform.claude.com', first_link.group(1)) if first_link else append_anchor(base_link, summary)
            title = choose_release_title(summary, emphasized, link_texts[0] if link_texts else '', first_sentence(summary))
            entries.append(FeedEntry(
                date=published,
                category='anthropic',
                source='Anthropic Release Notes',
                source_type='release-notes',
                title_en=title,
                summary_en=summary,
                url=append_anchor(link, title) if first_link is None else link,
                tags=unique_tags([title, 'anthropic', 'release-notes']),
            ))
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


def summarize_items(items: list[dict]) -> dict:
    source_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for item in items:
        source_counts[item['source']] = source_counts.get(item['source'], 0) + 1
        source_type = item.get('sourceType', 'missing')
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        category = item['category']
        category_counts[category] = category_counts.get(category, 0) + 1
    return {
        'totalItems': len(items),
        'sources': dict(sorted(source_counts.items())),
        'sourceTypes': dict(sorted(source_type_counts.items())),
        'categories': dict(sorted(category_counts.items())),
    }


def validate_digest_health(
    fresh_digest: list[dict],
    previous_digest: list[dict],
    config: dict[str, int | float | set[str]],
) -> list[str]:
    issues: list[str] = []
    current_summary = summarize_items(fresh_digest)
    previous_summary = summarize_items(previous_digest)
    min_active_items = int(config['min_active_items'])
    total_drop_ratio = float(config['total_drop_ratio'])
    source_drop_ratio = float(config['source_drop_ratio'])
    source_baseline = int(config['source_baseline'])
    required_sources = set(config['required_sources'])
    optional_sources = set(config['optional_sources'])

    if current_summary['totalItems'] < min_active_items:
        issues.append(
            f"Active digest only has {current_summary['totalItems']} items, below minimum threshold {min_active_items}."
        )

    previous_total = previous_summary['totalItems']
    current_total = current_summary['totalItems']
    total_drop_floor = max(min_active_items, int(previous_total * total_drop_ratio))
    if previous_total >= min_active_items and current_total < total_drop_floor:
        issues.append(
            f'Active digest dropped sharply from {previous_total} to {current_total} items.'
        )

    current_sources = current_summary['sources']
    previous_sources = previous_summary['sources']
    for source in sorted(required_sources):
        if current_sources.get(source, 0) == 0:
            issues.append(f'Missing required source: {source}.')

    for source, previous_count in previous_sources.items():
        if source in optional_sources or previous_count < source_baseline:
            continue
        current_count = current_sources.get(source, 0)
        minimum_allowed = max(1, int(previous_count * source_drop_ratio))
        if current_count < minimum_allowed:
            issues.append(
                f'Source {source} dropped from {previous_count} to {current_count}, below guard threshold {minimum_allowed}.'
            )

    return issues


def emit_report(report: dict) -> None:
    report_path = Path(os.environ.get('DIGEST_REPORT_PATH', REPORT_PATH))
    write_json(report_path, report)


def main() -> int:
    today = get_today()
    cutoff = subtract_months(today, WINDOW_MONTHS)

    existing_by_url, existing_archive = load_existing_items()
    translation_cache = load_translation_cache()
    translator = TranslationService(translation_cache)
    previous_digest = []
    if DIGEST_PATH.exists():
        previous_digest = json.loads(DIGEST_PATH.read_text(encoding='utf-8')).get('items', [])

    fresh_entries = (
        parse_anthropic_entries(cutoff)
        + parse_anthropic_release_entries(cutoff)
        + parse_openai_entries(cutoff)
        + parse_openai_changelog_entries(cutoff)
        + parse_google_entries(cutoff)
        + parse_google_release_entries(cutoff)
        + parse_github_entries(cutoff)
        + parse_github_changelog_entries(cutoff)
    )
    fresh_digest = materialize(fresh_entries, existing_by_url, translator)
    fresh_digest = [item for item in fresh_digest if date.fromisoformat(item['date']) >= cutoff]
    fresh_digest.sort(key=lambda item: (item['date'], item['id']), reverse=True)

    archive_items = merge_archive(existing_archive, previous_digest, fresh_digest, cutoff)

    validation_issues = []
    validation_config = get_validation_config()
    if os.environ.get('DIGEST_SKIP_VALIDATION') != '1':
        validation_issues = validate_digest_health(fresh_digest, previous_digest, validation_config)

    report = {
        'generatedAt': datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'today': today.isoformat(),
        'windowMonths': WINDOW_MONTHS,
        'active': summarize_items(fresh_digest),
        'archive': {'totalItems': len(archive_items)},
        'validation': {
            'passed': not validation_issues,
            'issues': validation_issues,
            'config': {
                'minActiveItems': validation_config['min_active_items'],
                'totalDropRatio': validation_config['total_drop_ratio'],
                'sourceDropRatio': validation_config['source_drop_ratio'],
                'sourceBaseline': validation_config['source_baseline'],
                'requiredSources': sorted(validation_config['required_sources']),
                'optionalSources': sorted(validation_config['optional_sources']),
            },
        },
        'translation': translator.stats(),
    }
    emit_report(report)

    if validation_issues:
        for issue in validation_issues:
            print(f'VALIDATION ERROR: {issue}', file=sys.stderr)
        return 1

    save_translation_cache(translation_cache)

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
    print('Source counts: ' + ', '.join(f"{name}={count}" for name, count in report['active']['sources'].items()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())