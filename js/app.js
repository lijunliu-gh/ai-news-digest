/* ═══════════════════════════════════════════════
   AI News Digest — App Logic
   ═══════════════════════════════════════════════ */

(function () {
  'use strict';

  const CATEGORY_LABELS = {
    all: 'All',
    github: 'GitHub',
    anthropic: 'Anthropic',
    openai: 'OpenAI',
    google: 'Google',
  };

  /* ---------- i18n ---------- */
  const I18N = {
    zh: {
      heroSub: '聚合近三个月 GitHub、Anthropic、OpenAI、Google 四大 AI 平台的官方产品更新',
      statTotal: '总数', statToday: '今日', statCategories: '分类',
      filterAll: '全部',
      themeToggleAria: '切换明暗主题',
      sourceTypeNews: '新闻',
      sourceTypeChangelog: '变更日志',
      sourceTypeReleaseNotes: '发布说明',
      monthFilterLabel: '月份',
      monthFilterAll: '全部月份',
      searchPlaceholder: '搜索标题、摘要、标签…',
      emptyState: '没有找到匹配的内容。',
      footerCredit: 'AI News Digest &mdash; 由 <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a> 策划',
      footerDisclaimer: '数据通过自动化定时更新，与所列公司无隶属关系。',
      trendTitle: '更新频率趋势',
      trendTooltipSuffix: '条更新',
      item: '条', items: '条',
      months: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      dateFmt: (y, m, d, months) => `${y}年${months[m]}${d}日`,
    },
    ja: {
      heroSub: '過去3か月分の GitHub、Anthropic、OpenAI、Google による公式プロダクト更新をまとめて確認できます',
      statTotal: '合計', statToday: '今日', statCategories: 'カテゴリ',
      filterAll: 'すべて',
      themeToggleAria: 'ライト/ダークテーマを切り替え',
      sourceTypeNews: 'ニュース',
      sourceTypeChangelog: '変更履歴',
      sourceTypeReleaseNotes: 'リリースノート',
      monthFilterLabel: '月別',
      monthFilterAll: 'すべての月',
      searchPlaceholder: 'タイトル、要約、タグを検索…',
      emptyState: '一致する項目が見つかりません。',
      footerCredit: 'AI News Digest &mdash; <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a> がキュレーション',
      footerDisclaimer: 'データは自動で定期更新されます。掲載企業とは無関係です。',
      trendTitle: '更新頻度トレンド',
      trendTooltipSuffix: '件の更新',
      item: '件', items: '件',
      months: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      dateFmt: (y, m, d, months) => `${y}年${months[m]}${d}日`,
    },
    en: {
      heroSub: 'Track official product updates from the past three months across GitHub, Anthropic, OpenAI, and Google',
      statTotal: 'Total', statToday: 'Today', statCategories: 'Categories',
      filterAll: 'All',
      themeToggleAria: 'Toggle light and dark theme',
      sourceTypeNews: 'News',
      sourceTypeChangelog: 'Changelog',
      sourceTypeReleaseNotes: 'Release Notes',
      monthFilterLabel: 'Month',
      monthFilterAll: 'All months',
      searchPlaceholder: 'Search titles, summaries, tags…',
      emptyState: 'No matching items found.',
      footerCredit: 'AI News Digest &mdash; curated by <a href="https://roundtableailab.org" target="_blank" rel="noopener">RoundTable AI Lab</a>',
      footerDisclaimer: 'Data updated automatically on a schedule. Not affiliated with any listed company.',
      trendTitle: 'Update Frequency Trend',
      trendTooltipSuffix: 'updates',
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
    document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
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
        populateMonthFilter();
        render();
        renderTrendChart();
      });
    });
  }

  let allItems = [];
  let activeCategory = 'all';
  let activeSourceType = 'all';
  let activeMonth = 'all';
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
    bindSourceTypeButtons();
    bindMonthFilter();
    populateMonthFilter();
    bindSearch();
    bindLangSwitcher();
    applyI18n();
    render();
    renderTrendChart();
    initBackToTop();
  }

  /* ---------- Stats ---------- */
  function renderStats() {
    const today = new Date().toISOString().slice(0, 10);
    const todayCount = allItems.filter(i => i.date === today).length;
    const cats = new Set(allItems.map(i => i.category));

    setText('stat-total', allItems.length);
    setText('stat-today', todayCount);
    setText('stat-sources', cats.size);

    // Items filtered by current source type (for category counts)
    const byType = activeSourceType === 'all'
      ? allItems
      : allItems.filter(i => (i.sourceType || 'news') === activeSourceType);

    // Items filtered by current category (for type counts)
    const byCat = activeCategory === 'all'
      ? allItems
      : allItems.filter(i => i.category === activeCategory);

    // Update category filter counts (scoped to active source type)
    document.querySelectorAll('.filter-btn').forEach(btn => {
      const cat = btn.dataset.cat;
      const countEl = btn.querySelector('.count');
      if (!countEl) return;
      const c = cat === 'all' ? byType.length : byType.filter(i => i.category === cat).length;
      countEl.textContent = c;
    });

    // Update source type counts (scoped to active category)
    document.querySelectorAll('.type-btn').forEach(btn => {
      const type = btn.dataset.type;
      const countEl = btn.querySelector('.count');
      if (!countEl) return;
      const c = type === 'all' ? byCat.length : byCat.filter(i => (i.sourceType || 'news') === type).length;
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

  function bindSourceTypeButtons() {
    document.querySelectorAll('.type-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        activeSourceType = btn.dataset.type;
        document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        render();
      });
    });
  }

  function bindMonthFilter() {
    const select = document.getElementById('month-filter');
    if (!select) return;

    select.addEventListener('change', () => {
      activeMonth = select.value;
      render();
    });
  }

  function populateMonthFilter() {
    const select = document.getElementById('month-filter');
    if (!select) return;

    const months = [...new Set(allItems.map(item => item.date.slice(0, 7)))].sort((a, b) => b.localeCompare(a));
    if (activeMonth !== 'all' && !months.includes(activeMonth)) {
      activeMonth = 'all';
    }

    const options = [`<option value="all">${escapeHtml(t('monthFilterAll'))}</option>`];
    for (const month of months) {
      const selected = month === activeMonth ? ' selected' : '';
      options.push(`<option value="${escapeHtml(month)}"${selected}>${escapeHtml(formatMonth(month))}</option>`);
    }

    select.innerHTML = options.join('');
    select.value = activeMonth;
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
    renderStats();

    const container = document.getElementById('feed');
    if (!container) return;

    let filtered = allItems;

    // Apply category filter
    if (activeCategory !== 'all') {
      filtered = filtered.filter(i => i.category === activeCategory);
    }

    // Apply source type filter
    if (activeSourceType !== 'all') {
      filtered = filtered.filter(i => (i.sourceType || 'news') === activeSourceType);
    }

    if (activeMonth !== 'all') {
      filtered = filtered.filter(i => i.date.startsWith(activeMonth));
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
      renderMonthIndicatorFromFeed();
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
    let lastMonth = '';
    for (const [date, items] of groups) {
      const monthKey = date.slice(0, 7);
      const monthAttr = monthKey !== lastMonth ? ` data-month="${monthKey}" id="month-${monthKey}"` : '';
      if (monthKey !== lastMonth) lastMonth = monthKey;
      html += `<div class="date-group"${monthAttr}>`;
      html += `<div class="date-label">${formatDate(date)} <span class="day-count">${items.length} ${items.length > 1 ? t('items') : t('item')}</span></div>`;
      for (const item of items) {
        html += renderCard(item, idx++);
      }
      html += `</div>`;
    }

    container.innerHTML = html;
    renderMonthIndicatorFromFeed();
  }

  function renderCard(item, idx) {
    const catLabel = CATEGORY_LABELS[item.category] || item.category;
    const tagsHtml = item.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');
    const delay = Math.min(idx * 0.04, 0.6);
    const title = localized(item.title);
    const summary = localized(item.summary);
    const sourceType = resolveSourceType(item);
    return `
      <a class="card" data-cat="${escapeHtml(item.category)}" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" style="animation-delay:${delay}s">
        <div class="card-top">
          <span class="card-cat" data-cat="${escapeHtml(item.category)}">${escapeHtml(catLabel)}</span>
          <div class="card-source-meta">
            <span class="source-type-badge">${escapeHtml(sourceType)}</span>
            <span class="card-source">${escapeHtml(item.source)}</span>
          </div>
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

  function formatMonth(monthStr) {
    const [y, m] = monthStr.split('-');
    const monthIndex = parseInt(m, 10) - 1;
    const lang = I18N[currentLang] || I18N.zh;
    if (currentLang === 'en') return `${lang.months[monthIndex]} ${y}`;
    return `${y}年${lang.months[monthIndex]}`;
  }

  function resolveSourceType(item) {
    const type = item.sourceType || inferSourceType(item.source || '');
    if (type === 'changelog') return t('sourceTypeChangelog');
    if (type === 'release-notes') return t('sourceTypeReleaseNotes');
    return t('sourceTypeNews');
  }

  function inferSourceType(source) {
    const normalized = source.toLowerCase();
    if (normalized.includes('changelog')) return 'changelog';
    if (normalized.includes('release notes')) return 'release-notes';
    return 'news';
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

  /* ---------- Trend Chart ---------- */
  const CHART_COLORS = {
    github:    { line: '#00a4ef', fill: 'rgba(0, 164, 239, 0.08)' },
    anthropic: { line: '#d4a574', fill: 'rgba(212, 165, 116, 0.08)' },
    openai:    { line: '#10a37f', fill: 'rgba(16, 163, 127, 0.08)' },
    google:    { line: '#ea4335', fill: 'rgba(234, 67, 53, 0.08)' },
  };

  let trendChart = null;

  function buildTrendData() {
    // Collect all YYYY-MM keys, sorted ascending
    const monthSet = new Set();
    for (const item of allItems) {
      monthSet.add(item.date.slice(0, 7));
    }
    const months = [...monthSet].sort();

    // Count per category per month
    const cats = ['github', 'anthropic', 'openai', 'google'];
    const series = {};
    for (const cat of cats) {
      series[cat] = months.map(m => allItems.filter(i => i.category === cat && i.date.startsWith(m)).length);
    }

    // Format labels
    const labels = months.map(m => {
      const [y, mon] = m.split('-');
      const idx = parseInt(mon, 10) - 1;
      const lang = I18N[currentLang] || I18N.zh;
      if (currentLang === 'en') return `${lang.months[idx]} ${y}`;
      return `${y}年${lang.months[idx]}`;
    });

    return { labels, months, series, cats };
  }

  function renderTrendChart() {
    const canvas = document.getElementById('trend-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const { labels, series, cats } = buildTrendData();
    if (labels.length === 0) return;

    const isDark = (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const tickColor = isDark ? '#8888a0' : '#555570';

    const datasets = cats.map(cat => ({
      label: CATEGORY_LABELS[cat] || cat,
      data: series[cat],
      borderColor: CHART_COLORS[cat].line,
      backgroundColor: CHART_COLORS[cat].fill,
      borderWidth: 2.5,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: CHART_COLORS[cat].line,
      pointBorderColor: isDark ? '#12121a' : '#ffffff',
      pointBorderWidth: 2,
      tension: 0.35,
      fill: true,
    }));

    const tooltipSuffix = t('trendTooltipSuffix');

    if (trendChart) {
      trendChart.data.labels = labels;
      trendChart.data.datasets = datasets;
      trendChart.options.scales.x.grid.color = gridColor;
      trendChart.options.scales.y.grid.color = gridColor;
      trendChart.options.scales.x.ticks.color = tickColor;
      trendChart.options.scales.y.ticks.color = tickColor;
      trendChart.update('none');
      return;
    }

    trendChart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: {
              boxWidth: 12,
              boxHeight: 12,
              borderRadius: 3,
              useBorderRadius: true,
              padding: 16,
              font: { family: "'Inter', sans-serif", size: 12, weight: '500' },
              color: tickColor,
            },
          },
          tooltip: {
            backgroundColor: isDark ? 'rgba(18,18,26,0.95)' : 'rgba(255,255,255,0.95)',
            titleColor: isDark ? '#e0e0e8' : '#1a1a2e',
            bodyColor: isDark ? '#8888a0' : '#555570',
            borderColor: isDark ? 'rgba(30,30,46,0.8)' : 'rgba(200,200,220,0.5)',
            borderWidth: 1,
            cornerRadius: 8,
            padding: 10,
            bodyFont: { family: "'Inter', sans-serif", size: 12 },
            titleFont: { family: "'Inter', sans-serif", size: 13, weight: '600' },
            callbacks: {
              label: function(ctx) {
                return `${ctx.dataset.label}: ${ctx.parsed.y} ${tooltipSuffix}`;
              }
            }
          },
        },
        scales: {
          x: {
            grid: { color: gridColor, drawBorder: false },
            ticks: {
              color: tickColor,
              font: { family: "'Inter', sans-serif", size: 11 },
              maxRotation: 0,
            },
            border: { display: false },
          },
          y: {
            beginAtZero: true,
            grid: { color: gridColor, drawBorder: false },
            ticks: {
              color: tickColor,
              font: { family: "'JetBrains Mono', monospace", size: 11 },
              stepSize: 1,
              precision: 0,
            },
            border: { display: false },
          },
        },
      },
    });
  }

  /* ---------- Theme ---------- */
  function syncThemeCheckbox() {
    const cb = document.getElementById('theme-checkbox');
    if (cb) cb.checked = (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
  }

  window.toggleTheme = function () {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch {}
    syncThemeCheckbox();
    renderTrendChart();
  };

  // Restore saved theme
  (function () {
    try {
      const saved = localStorage.getItem('theme');
      if (saved) document.documentElement.setAttribute('data-theme', saved);
    } catch {}
    syncThemeCheckbox();
  })();

  /* ---------- Back to Top ---------- */
  function initBackToTop() {
    const btn = document.getElementById('back-to-top');
    if (!btn) return;
    const threshold = 400;
    let ticking = false;

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          btn.classList.toggle('visible', window.scrollY > threshold);
          updateMonthIndicator();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Month Indicator ---------- */
  function renderMonthIndicatorFromFeed() {
    const container = document.getElementById('month-indicator');
    if (!container) return;

    const groups = document.querySelectorAll('[data-month]');
    if (groups.length === 0) {
      container.innerHTML = '';
      container.classList.remove('visible');
      return;
    }

    const seen = new Set();
    const items = [];
    groups.forEach(el => {
      const key = el.dataset.month;
      if (!key || seen.has(key)) return;
      seen.add(key);
      items.push({ key, el });
    });

    container.innerHTML = items.map(({ key }) =>
      `<a href="#month-${key}" data-month-link="${key}">${formatMonth(key)}</a>`
    ).join('');

    // Smooth scroll on click
    container.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById(link.getAttribute('href').slice(1));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });

    container.classList.toggle('visible', items.length > 1 && window.scrollY > 300);
  }

  function updateMonthIndicator() {
    const container = document.getElementById('month-indicator');
    if (!container) return;

    const links = container.querySelectorAll('a[data-month-link]');
    if (links.length === 0) return;

    container.classList.toggle('visible', links.length > 1 && window.scrollY > 300);

    // Find the month group currently in view
    const groups = document.querySelectorAll('[data-month]');
    let activeKey = '';
    const viewTop = window.scrollY + 120;

    groups.forEach(el => {
      if (el.offsetTop <= viewTop) {
        activeKey = el.dataset.month;
      }
    });

    links.forEach(link => {
      link.classList.toggle('active', link.dataset.monthLink === activeKey);
    });
  }

  /* ---------- Boot ---------- */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
