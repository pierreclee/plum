(function initStreak() {
  const KEY_VISIT = 'plum_lastVisit';
  const KEY_STREAK = 'plum_streak';

  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86_400_000).toDateString();
  const lastVisit = localStorage.getItem(KEY_VISIT);
  let streak = parseInt(localStorage.getItem(KEY_STREAK) || '0', 10);

  if (lastVisit !== today) {
    streak = lastVisit === yesterday ? streak + 1 : 1;
    localStorage.setItem(KEY_STREAK, streak);
    localStorage.setItem(KEY_VISIT, today);
  }

  const badge = document.getElementById('streakBadge');
  if (badge && streak > 0) {
    badge.textContent = streak === 1 ? '1 jour 🔥' : `${streak} jours 🔥`;
  }
})();
