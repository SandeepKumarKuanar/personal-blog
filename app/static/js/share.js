// ===== SHARE DROPDOWN =====
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('shareToggle');
  const dropdown = document.getElementById('shareDropdown');
  const options = dropdown.querySelectorAll('.share-option');

  // Toggle dropdown
  toggle.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.share-wrapper')) {
      dropdown.classList.remove('open');
    }
  });

  // Get post data
  function getPostData() {
    const title = document.querySelector('.post-title')?.textContent?.trim() || '';
    const url = window.location.href;
    return { title, url };
  }

  // Get share text for X
  function getXShareText() {
    const post = getPostData();
    return `"Just read: ${post.title}"`;
  }

  // Build share URL
  function buildShareUrl(base, params) {
    const url = new URL(base);
    Object.keys(params).forEach(key => {
      if (params[key]) {
        url.searchParams.append(key, params[key]);
      }
    });
    return url.toString();
  }

  // Handle share options
  options.forEach(option => {
    option.addEventListener('click', function(e) {
      const platform = this.dataset.platform;
      const post = getPostData();
      const baseUrl = post.url;

      switch (platform) {
        case 'copy':
          const copyUrl = baseUrl + '?utm_source=copy&utm_medium=direct&utm_campaign=blog_post';
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(copyUrl).then(() => {
              showCopyFeedback(this, '✅ Link copied!');
            }).catch(() => {
              fallbackCopy(copyUrl, this);
            });
          } else {
            fallbackCopy(copyUrl, this);
          }
          break;

        case 'x': {
          const shareText = getXShareText();
          const xUrl = buildShareUrl('https://x.com/intent/tweet', {
            text: shareText,
            url: baseUrl + '?utm_source=x&utm_medium=social&utm_campaign=blog_post',
            via: 'kuanar_sandeep',
          });
          window.open(xUrl, '_blank');
          break;
        }

        case 'linkedin': {
          // LinkedIn's official sharing URL
          const linkedinUrl = buildShareUrl('https://www.linkedin.com/sharing/share-offsite/', {
            url: baseUrl + '?utm_source=linkedin&utm_medium=social&utm_campaign=blog_post',
          });
          window.open(linkedinUrl, '_blank');
          break;
        }
      }

      dropdown.classList.remove('open');
    });
  });

  // Copy fallback
  function fallbackCopy(text, btn) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      showCopyFeedback(btn, '✅ Link copied!');
    } catch (err) {
      showCopyFeedback(btn, '⚠️ Could not copy');
    }
    document.body.removeChild(textarea);
  }

  // Show feedback on the button
  function showCopyFeedback(btn, message) {
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span style="display:flex;align-items:center;gap:0.4rem;">${message}</span>`;
    setTimeout(() => {
      btn.innerHTML = originalText;
    }, 2000);
  }
});
