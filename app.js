/* app.js \u2014 Fund Dashboard Application Logic */
(function () {
  'use strict';

  // ---- Helpers ----
  const $ = (s, p) => (p || document).querySelector(s);
  const $$ = (s, p) => [...(p || document).querySelectorAll(s)];

  function fmtNum(n, decimals) {
    if (n == null || isNaN(n)) return '\u2014';
    return n.toLocaleString('zh-CN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function fmtPct(n) {
    if (n == null || isNaN(n)) return '\u2014';
    const sign = n > 0 ? '+' : '';
    return sign + n.toFixed(2) + '%';
  }

  function fmtYi(n) {
    if (n == null || isNaN(n)) return '\u2014';
    const sign = n > 0 ? '+' : '';
    return sign + n.toFixed(2) + '\u4ebf';
  }

  function colorClass(val) {
    if (val == null || isNaN(val)) return 'val-flat';
    if (val > 0) return 'val-up';
    if (val < 0) return 'val-down';
    return 'val-flat';
  }

  // ---- Theme Toggle ----
  (function initTheme() {
    const toggle = $('[data-theme-toggle]');
    const root = document.documentElement;
    let theme = 'dark';
    root.setAttribute('data-theme', theme);
    if (toggle) {
      toggle.addEventListener('click', () => {
        theme = theme === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', theme);
      });
    }
  })();

  // ---- Data ----
  const data = FUND_DATA;

  // ---- Header ----
  function renderHeader() {
    const meta = data.metadata;
    $('#tradingDate').textContent = meta.trading_date;
    $('#updateTime').textContent = '\u66f4\u65b0: ' + meta.updated_at;

    // Time bar
    $('#lastUpdate').textContent = meta.updated_at + '\uff08\u5317\u4eac\u65f6\u95f4\uff09';

    // Calculate next update: next weekday at 16:30 Beijing time
    const parts = meta.updated_at.split(/[\-\s:]/);
    const updatedDate = new Date(Date.UTC(
      parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]),
      parseInt(parts[3]) - 8, parseInt(parts[4]), parseInt(parts[5] || 0)
    ));
    const now = new Date();
    const ref = now > updatedDate ? now : updatedDate;
    // Start from ref, find next weekday
    const next = new Date(ref);
    // Set to Beijing 16:30 = UTC 08:30
    next.setUTCHours(8, 30, 0, 0);
    // If already past 16:30 Beijing today, move to tomorrow
    if (next <= ref) {
      next.setUTCDate(next.getUTCDate() + 1);
    }
    // Skip weekends (Sat=6, Sun=0)
    let dow = next.getUTCDay();
    if (dow === 0) next.setUTCDate(next.getUTCDate() + 1);
    else if (dow === 6) next.setUTCDate(next.getUTCDate() + 2);

    const y = next.getUTCFullYear();
    const m = String(next.getUTCMonth() + 1).padStart(2, '0');
    const d = String(next.getUTCDate()).padStart(2, '0');
    const weekdays = ['\u5468\u65e5', '\u5468\u4e00', '\u5468\u4e8c', '\u5468\u4e09', '\u5468\u56db', '\u5468\u4e94', '\u5468\u516d'];
    const wd = weekdays[next.getUTCDay()];
    $('#nextUpdate').textContent = `${y}-${m}-${d} 16:30 ${wd}\uff08\u5317\u4eac\u65f6\u95f4\uff09`;
  }

  // ---- Index Cards ----
  function renderIndexCards() {
    const container = $('#indexCards');
    container.innerHTML = data.indices.map(idx => {
      const cc = colorClass(idx.change_pct);
      return `
        <div class="idx-card">
          <div class="idx-name">${idx.name}</div>
          <div class="idx-price ${cc}">${fmtNum(idx.price, 2)}</div>
          <div class="idx-detail ${cc}">
            <span>${fmtPct(idx.change_pct)}</span>
            <span>${idx.change_amt > 0 ? '+' : ''}${fmtNum(idx.change_amt, 2)}</span>
          </div>
          <div class="idx-amp">\u632f\u5e45 ${fmtNum(idx.amplitude, 2)}%</div>
        </div>`;
    }).join('');
  }

  // ---- Heatmap ----
  function renderHeatmap() {
    const container = $('#heatmapContainer');
    const boards = [...data.industry_boards].sort((a, b) => b.amount - a.amount);

    // Compute sizes based on amount (trading value)
    const maxAmount = Math.max(...boards.map(b => b.amount));
    const minSize = 65;
    const maxSize = 160;

    container.innerHTML = boards.map(b => {
      const ratio = Math.sqrt(b.amount / maxAmount);
      const size = Math.round(minSize + ratio * (maxSize - minSize));

      // Color: red gradient for positive, green gradient for negative
      const pct = b.change_pct;
      let bg;
      if (pct > 5) bg = 'rgba(200,40,40,0.85)';
      else if (pct > 2) bg = 'rgba(185,55,55,0.75)';
      else if (pct > 0.5) bg = 'rgba(165,70,65,0.65)';
      else if (pct > 0) bg = 'rgba(140,85,80,0.55)';
      else if (pct === 0 || pct === -0) bg = 'rgba(100,100,100,0.5)';
      else if (pct > -0.5) bg = 'rgba(60,120,80,0.55)';
      else if (pct > -2) bg = 'rgba(40,130,75,0.65)';
      else if (pct > -5) bg = 'rgba(25,140,70,0.75)';
      else bg = 'rgba(15,150,65,0.85)';

      return `
        <div class="hm-cell" style="width:${size}px;height:${Math.round(size * 0.6)}px;background:${bg};flex-grow:${Math.round(ratio * 10)}" title="${b.name}: ${fmtPct(b.change_pct)} | \u9886\u6da8: ${b.leader_name} ${fmtPct(b.leader_change_pct)}">
          <span class="hm-name">${b.name}</span>
          <span class="hm-pct">${b.change_pct > 0 ? '+' : ''}${b.change_pct.toFixed(2)}%</span>
        </div>`;
    }).join('');
  }

  // ---- Fund Flow Table ----
  function renderFundFlow() {
    const tbody = $('#flowBody');
    tbody.innerHTML = data.fund_flow.map(row => {
      return `<tr>
        <td>${row.date}</td>
        <td class="${colorClass(row.main_net_inflow)}">${fmtYi(row.main_net_inflow)}</td>
        <td class="${colorClass(row.super_large_net)}">${fmtYi(row.super_large_net)}</td>
        <td class="${colorClass(row.large_net)}">${fmtYi(row.large_net)}</td>
        <td class="${colorClass(row.medium_net)}">${fmtYi(row.medium_net)}</td>
        <td class="${colorClass(row.small_net)}">${fmtYi(row.small_net)}</td>
      </tr>`;
    }).join('');
  }

  // ---- Fund Table ----
  let currentTab = 'top50';
  let currentSort = 'daily_return';
  let sortDir = 'desc';

  function getCurrentFunds() {
    if (currentTab === 'top50') return [...data.top_funds];
    // Category funds may not have a 'type' field, inject it from tab name
    return (data.category_funds[currentTab] || []).map(f => ({
      ...f,
      type: f.type || currentTab
    }));
  }

  function sortFunds(funds, key, dir) {
    return funds.sort((a, b) => {
      const va = a[key] != null ? a[key] : -Infinity;
      const vb = b[key] != null ? b[key] : -Infinity;
      return dir === 'desc' ? vb - va : va - vb;
    });
  }

  function renderFundTable() {
    let funds = getCurrentFunds();
    funds = sortFunds(funds, currentSort, sortDir);

    const tbody = $('#fundBody');
    tbody.innerHTML = funds.map((f, i) => {
      const rank = i + 1;
      let rankHtml;
      if (rank <= 3) {
        rankHtml = `<span class="rank-${rank}">${rank}</span>`;
      } else {
        rankHtml = rank;
      }

      const fType = f.type || '\u5176\u4ed6';
      const typeClass = 'type-' + fType;

      const pctCell = (val) => {
        if (val == null || isNaN(val)) return '<td class="val-flat">\u2014</td>';
        return `<td class="${colorClass(val)}">${fmtPct(val)}</td>`;
      };

      return `<tr>
        <td>${rankHtml}</td>
        <td>${f.code}</td>
        <td title="${f.name}">${f.name}</td>
        <td><span class="type-badge ${typeClass}">${fType}</span></td>
        ${pctCell(f.daily_return)}
        ${pctCell(f.week_1)}
        ${pctCell(f.month_1)}
        ${pctCell(f.month_3)}
        ${pctCell(f.month_6)}
        ${pctCell(f.year_1)}
        ${pctCell(f.ytd)}
        <td>${f.fee || '\u2014'}</td>
      </tr>`;
    }).join('');

    // Update sort arrows
    $$('.fund-table th.sortable').forEach(th => {
      const key = th.dataset.sort;
      const arrow = th.querySelector('.sort-arrow');
      th.classList.remove('sorted-desc', 'sorted-asc');
      if (key === currentSort) {
        th.classList.add(sortDir === 'desc' ? 'sorted-desc' : 'sorted-asc');
        arrow.textContent = sortDir === 'desc' ? '\u25bc' : '\u25b2';
      } else {
        arrow.textContent = '';
      }
    });
  }

  // Tab click
  function initTabs() {
    const nav = $('#tabNav');
    nav.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab-btn');
      if (!btn) return;
      $$('.tab-btn', nav).forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTab = btn.dataset.tab;
      currentSort = 'daily_return';
      sortDir = 'desc';
      renderFundTable();
    });
  }

  // Sort click
  function initSort() {
    $$('.fund-table th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (key === currentSort) {
          sortDir = sortDir === 'desc' ? 'asc' : 'desc';
        } else {
          currentSort = key;
          sortDir = 'desc';
        }
        renderFundTable();
      });
    });
  }

  // ---- Insights ----
  function renderInsights() {
    const grid = $('#insightsGrid');
    const funds = data.top_funds;
    const boards = data.industry_boards;
    const flow = data.fund_flow;

    // 1. Today's top fund
    const topFund = funds[0];
    const card1 = `
      <div class="insight-card">
        <div class="insight-label">\u4eca\u65e5\u6da8\u5e45\u6700\u9ad8\u57fa\u91d1</div>
        <div class="insight-value">
          ${topFund.name}
          <span class="highlight-up">(${fmtPct(topFund.daily_return)})</span>
        </div>
        <div class="insight-sub">\u57fa\u91d1\u4ee3\u7801 ${topFund.code} \u00b7 ${topFund.type} \u00b7 \u8fd11\u6708${fmtPct(topFund.month_1)}</div>
      </div>`;

    // 2. Top 3 industry sectors
    const topBoards = [...boards].sort((a, b) => b.change_pct - a.change_pct).slice(0, 3);
    const card2 = `
      <div class="insight-card">
        <div class="insight-label">\u4eca\u65e5\u6da8\u5e45\u884c\u4e1a\u677f\u5757 Top 3</div>
        <div class="insight-value">
          ${topBoards.map((b, i) => `${b.name} <span class="highlight-up">${fmtPct(b.change_pct)}</span>`).join('\u3001')}
        </div>
        <div class="insight-sub">\u9886\u6da8\u4e2a\u80a1: ${topBoards.map(b => b.leader_name).join('\u3001')}</div>
      </div>`;

    // 3. 5-day main flow
    const totalMain = flow.reduce((s, r) => s + r.main_net_inflow, 0);
    const mainColor = totalMain >= 0 ? 'highlight-up' : 'highlight-down';
    const card3 = `
      <div class="insight-card">
        <div class="insight-label">\u8fc7\u53bb5\u5929\u4e3b\u529b\u8d44\u91d1\u7d2f\u8ba1\u51c0\u6d41\u5165</div>
        <div class="insight-value">
          <span class="${mainColor}">${fmtYi(totalMain)}</span>
        </div>
        <div class="insight-sub">\u65e5\u5747\u51c0\u6d41\u5165 ${fmtYi(totalMain / flow.length)} \u00b7 \u6700\u8fd1\u4e00\u65e5 ${fmtYi(flow[flow.length - 1].main_net_inflow)}</div>
      </div>`;

    // 4. Consistently high performers
    // Find funds in top_funds that are in top 15 for daily AND month_1 AND month_3
    const byDaily = [...funds].sort((a, b) => (b.daily_return || 0) - (a.daily_return || 0));
    const byMonth1 = [...funds].sort((a, b) => (b.month_1 || 0) - (a.month_1 || 0));
    const byMonth3 = [...funds].sort((a, b) => (b.month_3 || 0) - (a.month_3 || 0));

    const top15Daily = new Set(byDaily.slice(0, 15).map(f => f.code));
    const top15Month1 = new Set(byMonth1.slice(0, 15).map(f => f.code));
    const top15Month3 = new Set(byMonth3.slice(0, 15).map(f => f.code));

    const consistent = funds.filter(f =>
      top15Daily.has(f.code) && top15Month1.has(f.code) && top15Month3.has(f.code)
    );

    let consistentHtml;
    if (consistent.length === 0) {
      consistentHtml = '<span style="color:var(--color-text-muted)">\u6682\u65e0\u540c\u65f6\u5728\u4e09\u4e2a\u7ef4\u5ea6\u6392\u540d\u524d\u5217\u7684\u57fa\u91d1</span>';
    } else {
      consistentHtml = consistent.map(f =>
        `${f.name} <span class="highlight-up">(\u65e5${fmtPct(f.daily_return)} / \u6708${fmtPct(f.month_1)} / 3\u6708${fmtPct(f.month_3)})</span>`
      ).join('<br>');
    }

    const card4 = `
      <div class="insight-card">
        <div class="insight-label">\u65e5/\u6708/3\u6708\u6da8\u5e45\u5747\u6392\u524d\u5217\u7684\u57fa\u91d1</div>
        <div class="insight-value">${consistentHtml}</div>
        <div class="insight-sub">\u7b5b\u9009\u6761\u4ef6: \u65e5\u6da8\u5e45\u3001\u8fd11\u6708\u3001\u8fd13\u6708\u5747\u6392\u540d\u524d15</div>
      </div>`;

    grid.innerHTML = card1 + card2 + card3 + card4;
  }

  // ---- News Section ----
  const categoryIcons = {
    '\u76d1\u7ba1\u653f\u7b56': '\u2696\ufe0f',
    '\u5e02\u573a\u52a8\u6001': '\ud83d\udcc8',
    '\u57fa\u91d1\u53d1\u884c': '\ud83c\udd95',
    '\u884c\u4e1a\u5206\u6790': '\ud83d\udd0d',
    '\u4eba\u4e8b\u53d8\u52a8': '\ud83d\udc64',
    '\u56fd\u9645\u89c6\u89d2': '\ud83c\udf0f'
  };

  let currentNewsFilter = 'all';

  function renderNews() {
    const list = $('#newsList');
    const newsData = data.news || [];

    const filtered = currentNewsFilter === 'all'
      ? newsData
      : newsData.filter(n => n.category === currentNewsFilter);

    if (filtered.length === 0) {
      list.innerHTML = '<div class="news-empty">\u6682\u65e0\u8be5\u5206\u7c7b\u65b0\u95fb</div>';
      return;
    }

    list.innerHTML = filtered.map(item => {
      const icon = categoryIcons[item.category] || '\ud83d\udcf0';
      return `
        <a class="news-item" href="${item.url}" target="_blank" rel="noopener">
          <div class="news-item-top">
            <span class="news-cat">${icon} ${item.category}</span>
            <span class="news-date">${item.date}</span>
          </div>
          <div class="news-title">${item.title}</div>
          <div class="news-summary">${item.summary}</div>
          <div class="news-source">\u6765\u6e90\uff1a${item.source}</div>
        </a>`;
    }).join('');
  }

  function initNewsFilters() {
    const container = $('#newsFilters');
    if (!container) return;
    container.addEventListener('click', (e) => {
      const btn = e.target.closest('.news-filter-btn');
      if (!btn) return;
      $$('.news-filter-btn', container).forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentNewsFilter = btn.dataset.filter;
      renderNews();
    });
  }

  // ---- Init ----
  function init() {
    renderHeader();
    renderIndexCards();
    renderHeatmap();
    renderFundFlow();
    renderFundTable();
    initTabs();
    initSort();
    renderInsights();
    renderNews();
    initNewsFilters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
