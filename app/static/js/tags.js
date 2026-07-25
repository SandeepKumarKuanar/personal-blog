// ===== Tag filtering logic =====
document.addEventListener('DOMContentLoaded', function() {
  // --- Tag click: toggle apply/remove ---
  const tags = document.querySelectorAll('.tag');
  tags.forEach(tag => {
    tag.addEventListener('click', function(e) {
      e.preventDefault();
      const tagName = this.dataset.tag;

      // Get current URL and query params
      const url = new URL(window.location.href);
      const params = url.searchParams;

      // Get all current tag params
      let currentTags = params.getAll('tag');

      // Toggle: if tag exists, remove it; else add it
      const index = currentTags.indexOf(tagName);
      if (index > -1) {
        currentTags.splice(index, 1);
      } else {
        currentTags.push(tagName);
      }

      // Clear all tag params and set new ones
      params.delete('tag');
      currentTags.forEach(t => params.append('tag', t));

      // Preserve mode
      const activeMode = document.querySelector('.mode-btn.active');
      if (activeMode) {
        params.set('mode', activeMode.dataset.mode);
      }

      // Redirect
      window.location.href = url.pathname + '?' + params.toString();
    });
  });

  // --- Mode toggle: OR / AND ---
  const modeBtns = document.querySelectorAll('.mode-btn');
  modeBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const url = new URL(window.location.href);
      url.searchParams.set('mode', this.dataset.mode);
      window.location.href = url.pathname + '?' + url.searchParams.toString();
    });
  });
});
