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

  let allItems = [];
  let activeCategory = 'all';
  let searchQuery = '';

  /* ---------- Init ---------- */
  async function init() {
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
      filtered = filtered.filter(i =>
        i.title.toLowerCase().includes(searchQuery) ||
        i.summary.toLowerCase().includes(searchQuery) ||
        i.tags.some(t => t.toLowerCase().includes(searchQuery)) ||
        i.source.toLowerCase().includes(searchQuery)
      );
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
      html += `<div class="date-label">${formatDate(date)} <span class="day-count">${items.length} item${items.length > 1 ? 's' : ''}</span></div>`;
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
    return `
      <a class="card" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" style="animation-delay:${delay}s">
        <div class="card-top">
          <span class="card-cat" data-cat="${escapeHtml(item.category)}">${escapeHtml(catLabel)}</span>
          <span class="card-source">${escapeHtml(item.source)}</span>
        </div>
        <div class="card-title">${escapeHtml(item.title)}</div>
        <div class="card-summary">${escapeHtml(item.summary)}</div>
        <div class="card-tags">${tagsHtml}</div>
      </a>`;
  }

  function renderEmpty() {
    return `
      <div class="empty-state">
        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <p>No matching items found.</p>
      </div>`;
  }

  /* ---------- Helpers ---------- */
  function formatDate(dateStr) {
    const [y, m, d] = dateStr.split('-');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}, ${y}`;
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
