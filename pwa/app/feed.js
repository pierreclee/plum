const API_BASE = (() => {
  const { hostname } = window.location;
  return hostname === 'localhost' || hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : '';
})();

async function loadFeed(category = null) {
  const feedEl = document.getElementById('feed');
  feedEl.innerHTML = '<div class="loading">Chargement…</div>';

  const params = new URLSearchParams({ limit: '20' });
  if (category) params.set('category', category);
  const url = `${API_BASE}/api/feed?${params}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { data } = await res.json();
    renderFeed(data);
  } catch (_err) {
    const cached = typeof caches !== 'undefined'
      ? await caches.match(url).catch(() => null)
      : null;
    if (cached) {
      const { data } = await cached.json();
      renderFeed(data);
      document.getElementById('offlineBanner').style.display = 'block';
    } else {
      feedEl.innerHTML = '<div class="loading">Impossible de charger les actualités.</div>';
    }
  }
}

function renderFeed(topics) {
  const feedEl = document.getElementById('feed');
  if (!topics || !topics.length) {
    feedEl.innerHTML = '<div class="loading">Aucune actualité pour le moment.</div>';
    return;
  }
  feedEl.innerHTML = topics.map((t) => {
    const count = parseInt(t.article_count, 10) || 0;
    return `
    <article class="card">
      <div class="card-category">${escapeHtml(t.category)}</div>
      <div class="card-title">${escapeHtml(t.title)}</div>
      ${t.summary ? `<div class="card-summary">${escapeHtml(t.summary)}</div>` : ''}
      <div class="card-meta">
        <span>${count} source${count > 1 ? 's' : ''}</span>
        ${t.sources.length ? `<span>${escapeHtml(t.sources.slice(0, 2).join(', '))}</span>` : ''}
        ${t.published_at ? `<span>${new Date(t.published_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}</span>` : ''}
      </div>
    </article>
  `;
  }).join('');
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

navigator.serviceWorker && navigator.serviceWorker.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'OFFLINE') {
    document.getElementById('offlineBanner').style.display = 'block';
  }
});

loadFeed(null);
