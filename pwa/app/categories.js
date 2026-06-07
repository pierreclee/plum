const CATEGORIES = ['france', 'monde', 'tech', 'eco', 'sport'];
let currentCategory = null;

(function initCategories() {
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

  nav.appendChild(makeBtn('Tout', null));
  CATEGORIES.forEach((cat) => {
    const label = cat.charAt(0).toUpperCase() + cat.slice(1);
    nav.appendChild(makeBtn(label, cat));
  });

  nav.querySelector('button').classList.add('active');
})();
