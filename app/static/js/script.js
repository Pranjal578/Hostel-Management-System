// ============================================================
// HOSTEL MANAGEMENT SYSTEM — PREMIUM JAVASCRIPT (2026)
// Covers: Dark Mode, Sticky Header, Mobile Menu, Toast,
//         Skeleton, Cookie Banner, Back-to-Top, Shortcuts,
//         Empty States, FAQs, Copy Button, Password Toggle,
//         Hover States, Custom Scrollbar, Form Helpers
// ============================================================

// ─────────────────────────────────────────────────────────────
// 1. DARK MODE TOGGLE
// ─────────────────────────────────────────────────────────────
(function initTheme() {
    // Inline in <head> already applies class — just wire the button here
    const btn = document.getElementById('darkModeToggle');
    if (!btn) return;

    function updateBtn() {
        const isDark = !document.documentElement.classList.contains('light-theme');
        btn.textContent = isDark ? '☀️' : '🌙';
        btn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        btn.setAttribute('aria-label', btn.getAttribute('title'));
    }

    updateBtn();

    btn.addEventListener('click', () => {
        document.documentElement.classList.toggle('light-theme');
        const isLight = document.documentElement.classList.contains('light-theme');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        updateBtn();
        showToast('Theme changed', isLight ? 'Switched to Light Mode ☀️' : 'Switched to Dark Mode 🌙', 'info', 2500);
    });
})();

// ─────────────────────────────────────────────────────────────
// 2. STICKY HEADER — scroll-shrink
// ─────────────────────────────────────────────────────────────
(function stickyHeader() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                navbar.classList.toggle('scrolled', window.scrollY > 40);
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
})();

// ─────────────────────────────────────────────────────────────
// 3. MOBILE MENU — full-screen overlay with animation
// ─────────────────────────────────────────────────────────────
(function mobileMenu() {
    const toggle = document.getElementById('menuToggle');
    const menu   = document.getElementById('navbarMenu');
    if (!toggle || !menu) return;

    let open = false;

    function setOpen(state) {
        open = state;
        toggle.textContent = open ? '✕' : '☰';
        toggle.setAttribute('aria-expanded', open);
        menu.classList.toggle('mobile-open', open);
        document.body.style.overflow = open ? 'hidden' : '';
    }

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        setOpen(!open);
    });

    // Close on nav link click
    menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => setOpen(false));
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (open && !e.target.closest('.navbar')) setOpen(false);
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && open) setOpen(false);
    });
})();

// ─────────────────────────────────────────────────────────────
// 4. TOAST NOTIFICATION SYSTEM
// ─────────────────────────────────────────────────────────────
const TOAST_ICONS = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };
const TOAST_TITLES = { success: 'Success', danger: 'Error', warning: 'Warning', info: 'Info' };

window.showToast = function(title, message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <span class="toast-icon">${TOAST_ICONS[type] || 'ℹ️'}</span>
        <div class="toast-body">
            <div class="toast-title">${title || TOAST_TITLES[type]}</div>
            ${message ? `<div class="toast-msg">${message}</div>` : ''}
        </div>
        <button class="toast-close" aria-label="Dismiss">&times;</button>
        <div class="toast-progress" style="animation-duration:${duration}ms"></div>
    `;

    function dismiss() {
        toast.classList.add('toast-out');
        toast.addEventListener('animationend', () => toast.remove(), { once: true });
    }

    toast.querySelector('.toast-close').addEventListener('click', dismiss);
    toast.addEventListener('click', dismiss);
    container.appendChild(toast);

    setTimeout(dismiss, duration);
    return toast;
};

// Legacy compatibility — keep showNotification as alias
window.showNotification = function(msg, type = 'info') {
    showToast(TOAST_TITLES[type] || 'Notice', msg, type);
};

// ─────────────────────────────────────────────────────────────
// 5. BACK TO TOP BUTTON
// ─────────────────────────────────────────────────────────────
(function backToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 300);
    }, { passive: true });

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();

// ─────────────────────────────────────────────────────────────
// 6. COOKIE CONSENT BANNER
// ─────────────────────────────────────────────────────────────
(function cookieBanner() {
    const banner  = document.getElementById('cookie-banner');
    const accept  = document.getElementById('cookie-accept');
    const decline = document.getElementById('cookie-decline');
    if (!banner) return;

    // Show if not already consented
    if (!localStorage.getItem('cookie-consent')) {
        setTimeout(() => banner.classList.add('visible'), 800);
    }

    function dismiss(choice) {
        banner.classList.remove('visible');
        localStorage.setItem('cookie-consent', choice);
        setTimeout(() => banner.remove(), 500);
    }

    accept?.addEventListener('click',  () => { dismiss('accepted'); showToast('Cookies Accepted', 'Your preferences have been saved.', 'success', 2500); });
    decline?.addEventListener('click', () => { dismiss('declined'); showToast('Cookies Declined', 'Only essential cookies are active.', 'info', 2500); });
})();

// ─────────────────────────────────────────────────────────────
// 7. KEYBOARD SHORTCUTS
// ─────────────────────────────────────────────────────────────
(function keyboardShortcuts() {
    const modal = document.getElementById('shortcuts-modal');
    if (!modal) return;

    function open()  { modal.classList.add('open');  document.body.style.overflow = 'hidden'; }
    function close() { modal.classList.remove('open'); document.body.style.overflow = ''; }

    document.addEventListener('keydown', (e) => {
        // ? or Shift+/ to open shortcuts
        if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
            if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
            e.preventDefault();
            modal.classList.contains('open') ? close() : open();
            return;
        }

        if (!modal.classList.contains('open')) {
            // Global shortcuts (only when modal is closed)
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); document.querySelector('#searchInput')?.focus(); }
            if (e.key === 'Escape') close();
        } else {
            if (e.key === 'Escape') close();
        }

        // Role-specific shortcuts
        if (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            if (e.key === 'g' && !e.ctrlKey) {
                // g + h = go home
            }
        }
    });

    // Close on outside click
    modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

    // Close button inside panel
    document.getElementById('shortcuts-close')?.addEventListener('click', close);
})();

// ─────────────────────────────────────────────────────────────
// 8. EXPANDABLE FAQ ACCORDION
// ─────────────────────────────────────────────────────────────
(function faqAccordion() {
    document.querySelectorAll('.faq-question').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.closest('.faq-item');
            const isOpen = item.classList.contains('open');

            // Close all others (single-open mode)
            document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));

            if (!isOpen) item.classList.add('open');
        });
    });
})();

// ─────────────────────────────────────────────────────────────
// 9. COPY BUTTON (enhanced with visual feedback)
// ─────────────────────────────────────────────────────────────
(function copyButtons() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-copy');
        if (!btn) return;

        const text = btn.getAttribute('data-copy');
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            const label = btn.querySelector('.copy-label');
            const icon  = btn.querySelector('.copy-icon');
            const orig  = label?.textContent;
            const origIcon = icon?.textContent;

            btn.classList.add('copied');
            if (label) label.textContent = 'Copied!';
            if (icon)  icon.textContent  = '✓';

            setTimeout(() => {
                btn.classList.remove('copied');
                if (label) label.textContent = orig;
                if (icon)  icon.textContent  = origIcon;
            }, 2000);

            showToast('Copied!', 'Text copied to clipboard.', 'success', 2000);
        }).catch(() => showToast('Error', 'Could not copy to clipboard.', 'danger'));
    });
})();

// ─────────────────────────────────────────────────────────────
// 10. PASSWORD VISIBILITY TOGGLE
// ─────────────────────────────────────────────────────────────
(function passwordToggles() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.toggle-password');
        if (!btn) return;

        const targetSel = btn.getAttribute('data-target');
        const input = targetSel ? document.querySelector(targetSel) : btn.previousElementSibling;
        if (!input) return;

        const isHidden = input.type === 'password';
        input.type = isHidden ? 'text' : 'password';
        btn.textContent = isHidden ? '🙈' : '👁️';
        btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
    });
})();

// ─────────────────────────────────────────────────────────────
// 11. AUTO-DISMISS ALERTS (with close button support)
// ─────────────────────────────────────────────────────────────
(function alertSystem() {
    // Add close buttons to existing server-rendered alerts
    document.querySelectorAll('.alert').forEach(alert => {
        if (!alert.querySelector('.alert-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'alert-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.setAttribute('aria-label', 'Dismiss alert');
            closeBtn.addEventListener('click', () => dismissAlert(alert));
            alert.appendChild(closeBtn);
        }
        // Auto-dismiss after 6 seconds
        setTimeout(() => dismissAlert(alert), 6000);
    });

    function dismissAlert(el) {
        el.style.transition = 'opacity 0.4s ease, transform 0.4s ease, max-height 0.4s ease, margin 0.4s ease';
        el.style.opacity = '0';
        el.style.transform = 'translateX(10px)';
        el.style.maxHeight = '0';
        el.style.marginBottom = '0';
        el.style.overflow = 'hidden';
        setTimeout(() => el.remove(), 450);
    }
})();

// ─────────────────────────────────────────────────────────────
// 12. FORM VALIDATION + HELPERS
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {

    // Form required field validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            form.querySelectorAll('[required]').forEach(field => {
                const ok = field.value.trim() !== '';
                field.style.borderColor = ok ? '' : 'var(--danger)';
                if (!ok) isValid = false;
            });
            if (!isValid) {
                e.preventDefault();
                showToast('Validation Error', 'Please fill in all required fields.', 'danger');
            }
        });
    });

    // Password match validation
    const pwField  = document.getElementById('password');
    const cpwField = document.getElementById('confirm_password');
    if (pwField && cpwField) {
        cpwField.addEventListener('input', () => {
            const match = pwField.value === cpwField.value;
            cpwField.setCustomValidity(match ? '' : 'Passwords do not match');
            cpwField.style.borderColor = match ? '' : 'var(--danger)';
        });
    }

    // Delete confirmation
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', e => {
            if (!confirm('Are you sure? This action cannot be undone.')) e.preventDefault();
        });
    });

    // Phone input: numeric only, max 10 digits
    document.querySelectorAll('input[type="tel"]').forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    });

    // Room number: uppercase, no spaces
    const roomInput = document.getElementById('room_number');
    if (roomInput) {
        roomInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase().replace(/\s/g, '');
        });
    }

    // DOB max date
    document.querySelectorAll('input[type="date"][name="date_of_birth"]').forEach(input => {
        if (!input.value) {
            const today = new Date();
            const max = new Date(today.getFullYear() - 15, today.getMonth(), today.getDate());
            input.max = max.toISOString().split('T')[0];
        }
    });

    // ─── Loading state on form submit ───
    document.querySelectorAll('form button[type="submit"]').forEach(btn => {
        btn.closest('form')?.addEventListener('submit', function() {
            if (btn.form?.checkValidity() !== false) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Processing…';
            }
        });
    });

    // ─── Search filter ───
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const term = this.value.toLowerCase();
            document.querySelectorAll('tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
            });
        });
    }

    // ─── Sortable table headers ───
    document.querySelectorAll('th[data-sort]').forEach(header => {
        header.style.cursor = 'pointer';
        header.title = 'Click to sort';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows  = Array.from(tbody.querySelectorAll('tr'));
            const colIdx = Array.from(this.parentElement.children).indexOf(this);
            const asc = this.classList.contains('sort-asc');

            rows.sort((a, b) => {
                const av = a.cells[colIdx]?.textContent.trim() || '';
                const bv = b.cells[colIdx]?.textContent.trim() || '';
                return asc ? bv.localeCompare(av) : av.localeCompare(bv);
            });
            table.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            this.classList.add(asc ? 'sort-desc' : 'sort-asc');
            rows.forEach(r => tbody.appendChild(r));
        });
    });

    // ─── Image preview ───
    const imgInput = document.getElementById('profile_image');
    const imgPrev  = document.getElementById('imagePreview');
    if (imgInput && imgPrev) {
        imgInput.addEventListener('change', e => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = ev => { imgPrev.src = ev.target.result; };
                reader.readAsDataURL(file);
            }
        });
    }

    // ─── Smooth scroll ───
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
            const href = a.getAttribute('href');
            if (href.length > 1) {
                const target = document.querySelector(href);
                if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            }
        });
    });

    // ─── Print buttons ───
    document.querySelectorAll('.btn-print').forEach(btn => btn.addEventListener('click', () => window.print()));

    // ─── Auto-save draft ───
    document.querySelectorAll('form[data-draft]').forEach(form => {
        const id = form.getAttribute('data-draft');
        const stored = localStorage.getItem(`draft_${id}`);
        if (stored) {
            try {
                const data = JSON.parse(stored);
                Object.keys(data).forEach(k => {
                    const el = form.querySelector(`[name="${k}"]`);
                    if (el && !el.value) el.value = data[k];
                });
            } catch {}
        }
        form.addEventListener('input', () => {
            const d = Object.fromEntries(new FormData(form));
            localStorage.setItem(`draft_${id}`, JSON.stringify(d));
        });
        form.addEventListener('submit', () => localStorage.removeItem(`draft_${id}`));
    });

    // ─── Convert flash alerts to toasts (optional: uncomment to use) ───
    // document.querySelectorAll('.alert[data-toast]').forEach(el => {
    //     const type = el.classList.contains('alert-success') ? 'success' :
    //                  el.classList.contains('alert-danger')  ? 'danger'  :
    //                  el.classList.contains('alert-warning') ? 'warning' : 'info';
    //     showToast(null, el.textContent.trim(), type);
    //     el.remove();
    // });

}); // End DOMContentLoaded

// ─────────────────────────────────────────────────────────────
// 13. SKELETON LOADER HELPER
// ─────────────────────────────────────────────────────────────
/**
 * showSkeleton(container, template)
 * Inserts a skeleton placeholder inside the given container.
 * Call hideSkeleton(container) once data is ready.
 *
 * Example template: 'card' | 'list' | 'profile'
 */
window.showSkeleton = function(container, template = 'list', count = 3) {
    if (!container) return;
    const templates = {
        card: `<div class="skeleton skeleton-card"></div>`,
        list: `<div class="skeleton-row">
                   <div class="skeleton skeleton-avatar"></div>
                   <div style="flex:1">
                       <div class="skeleton skeleton-text"></div>
                       <div class="skeleton skeleton-text w-50"></div>
                   </div>
               </div>`,
        profile: `<div class="skeleton-row">
                      <div class="skeleton skeleton-avatar" style="width:96px;height:96px"></div>
                      <div style="flex:1">
                          <div class="skeleton skeleton-text w-50"></div>
                          <div class="skeleton skeleton-text w-75"></div>
                          <div class="skeleton skeleton-text w-25"></div>
                      </div>
                  </div>`
    };
    const html = Array(count).fill(templates[template] || templates.list).join('');
    container.innerHTML = `<div class="skeleton-placeholder">${html}</div>`;
};

window.hideSkeleton = function(container) {
    container?.querySelector('.skeleton-placeholder')?.remove();
};

// ─────────────────────────────────────────────────────────────
// 14. EMPTY STATE HELPER
// ─────────────────────────────────────────────────────────────
/**
 * showEmptyState(container, { icon, title, message, actionLabel, actionHref })
 */
window.showEmptyState = function(container, opts = {}) {
    if (!container) return;
    const {
        icon = '📭',
        title = 'Nothing here yet',
        message = '',
        actionLabel = '',
        actionHref  = '#'
    } = opts;
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <h3>${title}</h3>
            ${message ? `<p>${message}</p>` : ''}
            ${actionLabel ? `<a href="${actionHref}" class="btn btn-primary btn-sm">${actionLabel}</a>` : ''}
        </div>`;
};

// ─────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}
function validateEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); }
function validatePhone(phone) { return /^[0-9]{10}$/.test(phone); }
function generatePassword(length = 12) {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    return Array.from({ length }, () => charset[Math.floor(Math.random() * charset.length)]).join('');
}
