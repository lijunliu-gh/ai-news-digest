/* ═══════════════════════════════════════════════
   AI News Digest — App Logic
   ═══════════════════════════════════════════════ */

(function () {
  'use strict';

  const CATEGORY_LABELS = {
    all: 'All',
    microsoft: 'Microsoft / GitHub',
    anthropic: 'Anthropic',
    openai: 'OpenAI',
    google: 'Google',
  };

  /* ---------- i18n ---------- */
  const I18N = {
    zh: {
      heroSub: '关注 Microsoft / GitHub Copilot, Anthropic, OpenAI, Google 四大 AI 厂商的最新动态',
      statTotal: '总数', statToday: '今日', statCategories: '分类',
      filterAll: '全部',
      searchPlaceholder: '搜索标题、摘要、标签…',
      emptyState: '没有找到匹配的内容。',
      footerCredit: 'AI News Digest &mdash; 由 <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a> 策划',
      footerDisclaimer: '数据通过手动或自动化更新，与所列公司无隶属关系。',
      item: '条', items: '条',
      months: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      dateFmt: (y, m, d, months) => `${y}年${months[m]}${d}日`,
    },
    ja: {
      heroSub: 'Microsoft / GitHub Copilot, Anthropic, OpenAI, Google — 4大AIベンダーの最新ニュース',
      statTotal: '合計', statToday: '今日', statCategories: 'カテゴリ',
      filterAll: 'すべて',
      searchPlaceholder: 'タイトル、要約、タグを検索…',
      emptyState: '一致する項目が見つかりません。',
      footerCredit: 'AI News Digest &mdash; <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a> がキュレーション',
      footerDisclaimer: 'データは手動または自動で更新されます。掲載企業とは無関係です。',
      item: '件', items: '件',
      months: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      dateFmt: (y, m, d, months) => `${y}年${months[m]}${d}日`,
    },
    en: {
      heroSub: 'Stay updated with the latest from Microsoft / GitHub Copilot, Anthropic, OpenAI & Google',
      statTotal: 'Total', statToday: 'Today', statCategories: 'Categories',
      filterAll: 'All',
      searchPlaceholder: 'Search titles, summaries, tags…',
      emptyState: 'No matching items found.',
      footerCredit: 'AI News Digest &mdash; curated by <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a>',
      footerDisclaimer: 'Data updated manually or via automation. Not affiliated with any listed company.',
      item: 'item', items: 'items',
      months: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
      dateFmt: (y, m, d, months) => `${months[m]} ${d}, ${y}`,
    },
  };

  let currentLang = 'zh';

  function t(key) { return (I18N[currentLang] || I18N.zh)[key] || key; }
  function localized(field) { return (typeof field === 'object' && field !== null) ? (field[currentLang] || field.zh || field.en || '') : (field || ''); }

  function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      el.innerHTML = t(el.dataset.i18nHtml);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : currentLang === 'ja' ? 'ja' : 'en';
  }

  function bindLangSwitcher() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentLang = btn.dataset.lang;
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        try { localStorage.setItem('lang', currentLang); } catch {}
        applyI18n();
        render();
      });
    });
  }

  let allItems = [];
  let activeCategory = 'all';
  let searchQuery = '';

  /* ---------- Init ---------- */
  async function init() {
    // Restore saved language
    try {
      const savedLang = localStorage.getItem('lang');
      if (savedLang && I18N[savedLang]) {
        currentLang = savedLang;
        document.querySelectorAll('.lang-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.lang === currentLang);
        });
      }
    } catch {}

    try {
      const resp = await fetch('./data/digest.json');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      allItems = data.items.sort((a, b) => b.date.localeCompare(a.date));
    } catch (err) {
      console.error('Failed to load digest data:', err);
      allItems = [];
    }

    renderStats();
    bindFilterButtons();
    bindSearch();
    bindLangSwitcher();
    applyI18n();
    render();
  }

  /* ---------- Stats ---------- */
  function renderStats() {
    const today = new Date().toISOString().slice(0, 10);
    const todayCount = allItems.filter(i => i.date === today).length;
    const cats = new Set(allItems.map(i => i.category));

    setText('stat-total', allItems.length);
    setText('stat-today', todayCount);
    setText('stat-sources', cats.size);

    // Update filter counts
    document.querySelectorAll('.filter-btn').forEach(btn => {
      const cat = btn.dataset.cat;
      const countEl = btn.querySelector('.count');
      if (!countEl) return;
      const c = cat === 'all' ? allItems.length : allItems.filter(i => i.category === cat).length;
      countEl.textContent = c;
    });
  }

  /* ---------- Filters ---------- */
  function bindFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        activeCategory = btn.dataset.cat;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        render();
      });
    });
  }

  /* ---------- Search ---------- */
  function bindSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    let debounce;
    input.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        searchQuery = input.value.trim().toLowerCase();
        render();
      }, 200);
    });
  }

  /* ---------- Render ---------- */
  function render() {
    const container = document.getElementById('feed');
    if (!container) return;

    let filtered = allItems;

    // Apply category filter
    if (activeCategory !== 'all') {
      filtered = filtered.filter(i => i.category === activeCategory);
    }

    // Apply search
    if (searchQuery) {
      filtered = filtered.filter(i => {
        const title = localized(i.title).toLowerCase();
        const summary = localized(i.summary).toLowerCase();
        return title.includes(searchQuery) ||
          summary.includes(searchQuery) ||
          i.tags.some(t => t.toLowerCase().includes(searchQuery)) ||
          i.source.toLowerCase().includes(searchQuery);
      });
    }

    if (filtered.length === 0) {
      container.innerHTML = renderEmpty();
      return;
    }

    // Group by date
    const groups = new Map();
    for (const item of filtered) {
      if (!groups.has(item.date)) groups.set(item.date, []);
      groups.get(item.date).push(item);
    }

    let html = '';
    let idx = 0;
    for (const [date, items] of groups) {
      html += `<div class="date-group">`;
      html += `<div class="date-label">${formatDate(date)} <span class="day-count">${items.length} ${items.length > 1 ? t('items') : t('item')}</span></div>`;
      for (const item of items) {
        html += renderCard(item, idx++);
      }
      html += `</div>`;
    }

    container.innerHTML = html;
  }

  function renderCard(item, idx) {
    const catLabel = CATEGORY_LABELS[item.category] || item.category;
    const tagsHtml = item.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');
    const delay = Math.min(idx * 0.04, 0.6);
    const title = localized(item.title);
    const summary = localized(item.summary);
    return `
      <a class="card" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" style="animation-delay:${delay}s">
        <div class="card-top">
          <span class="card-cat" data-cat="${escapeHtml(item.category)}">${escapeHtml(catLabel)}</span>
          <span class="card-source">${escapeHtml(item.source)}</span>
        </div>
        <div class="card-title">${escapeHtml(title)}</div>
        <div class="card-summary">${escapeHtml(summary)}</div>
        <div class="card-tags">${tagsHtml}</div>
      </a>`;
  }

  function renderEmpty() {
    return `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <p>${escapeHtml(t('emptyState'))}</p>
      </div>`;
  }

  /* ---------- Helpers ---------- */
  function formatDate(dateStr) {
    const [y, m, d] = dateStr.split('-');
    const lang = I18N[currentLang] || I18N.zh;
    return lang.dateFmt(y, parseInt(m, 10) - 1, parseInt(d, 10), lang.months);
  }

  function escapeHtml(str) {
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  /* ---------- Theme ---------- */
  window.toggleTheme = function () {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch {}
  };

  // Restore saved theme
  (function () {
    try {
      const saved = localStorage.getItem('theme');
      if (saved) document.documentElement.setAttribute('data-theme', saved);
    } catch {}
  })();

  /* ---------- Boot ---------- */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
