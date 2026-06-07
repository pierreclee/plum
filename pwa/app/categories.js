const FALLBACK_CATEGORIES = ['france', 'monde', 'tech', 'eco', 'sport'];
let currentCategory = null;

async function initCategories() {
  const nav = document.getElementById('categoriesNav');

  function makeBtn(label, category) {
    const btn = document.createElement('button');
    btn.textContent = label;
    if (category === currentCategory) btn.classList.add('active');
    btn.addEventListener('click', () => {
      nav.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = category;
      if (typeof loadFeed === 'function') loadFeed(category);
    });
    return btn;
  }

  let categories = FALLBACK_CATEGORIES;
  try {
    const apiBase = window.API_BASE !== undefined
      ? window.API_BASE
      : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
          ? 'http://localhost:8000'
          : '');
    const res = await fetch(apiBase + '/api/categories');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (Array.isArray(data) && data.length) categories = data;
  } catch (_err) {
    categories = FALLBACK_CATEGORIES;
  }

  nav.appendChild(makeBtn('Tout', null));
  categories.forEach((cat) => {
    const label = cat.charAt(0).toUpperCase() + cat.slice(1);
    nav.appendChild(makeBtn(label, cat));
  });

  nav.querySelector('button').classList.add('active');
}

initCategories();
