document.addEventListener('alpine:init', () => {

  // ── Dark mode ──────────────────────────────────────────────────────
  Alpine.store('dark', {
    on: localStorage.getItem('darkMode') === 'true',
    toggle() {
      this.on = !this.on;
      localStorage.setItem('darkMode', this.on);
      document.documentElement.classList.toggle('dark', this.on);
    },
    init() {
      document.documentElement.classList.toggle('dark', this.on);
    }
  });

  // ── Toast notifications ────────────────────────────────────────────
  Alpine.store('toast', {
    messages: [],
    show(message, type = 'info', duration = 4000) {
      const id = Date.now() + Math.random();
      this.messages.push({ id, message, type });
      setTimeout(() => {
        this.messages = this.messages.filter(m => m.id !== id);
      }, duration);
    },
    success(msg) { this.show(msg, 'success'); },
    error(msg)   { this.show(msg, 'error');   },
    warning(msg) { this.show(msg, 'warning'); },
    info(msg)    { this.show(msg, 'info');    }
  });

  // Bridge Flask flash messages → Alpine toasts
  document.querySelectorAll('[data-flash]').forEach(el => {
    const type = el.dataset.flashType || 'info';
    Alpine.store('toast').show(el.dataset.flash, type);
    el.remove();
  });

  // ── Sidebar state ──────────────────────────────────────────────────
  Alpine.data('sidebar', () => ({
    open: false,
    toggle() { this.open = !this.open; }
  }));

  // ── Confirm dialog ─────────────────────────────────────────────────
  Alpine.data('confirmDialog', () => ({
    open: false,
    title: '',
    message: '',
    confirmText: 'تایید',
    cancelText: 'لغو',
    type: 'danger',
    onConfirm: null,
    show(title, message, onConfirm, type = 'danger') {
      this.title = title;
      this.message = message;
      this.onConfirm = onConfirm;
      this.type = type;
      this.confirmText = type === 'danger' ? 'حذف' : 'تایید';
      this.open = true;
    },
    confirm() {
      if (this.onConfirm) this.onConfirm();
      this.open = false;
    }
  }));

  // ── Search filter (for home page) ──────────────────────────────────
  Alpine.data('restaurantSearch', () => ({
    query: '',
    init() {
      this.query = '';
    },
    get filtered() {
      if (!this.query.trim()) return true;
      const q = this.query.toLowerCase();
      return (name, category, city) => {
        return name.toLowerCase().includes(q) ||
               category.toLowerCase().includes(q) ||
               city.toLowerCase().includes(q);
      };
    }
  }));

  // ── Auto-refresh polling ───────────────────────────────────────────
  Alpine.data('poller', () => ({
    interval: null,
    start(url, targetId, intervalMs = 30000) {
      this.interval = setInterval(async () => {
        try {
          const resp = await fetch(url);
          if (resp.ok) {
            const html = await resp.text();
            const target = document.getElementById(targetId);
            if (target) target.innerHTML = html;
          }
        } catch(e) {}
      }, intervalMs);
    },
    stop() {
      if (this.interval) clearInterval(this.interval);
    }
  }));
});
