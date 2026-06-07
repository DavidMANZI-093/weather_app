// Theme: 'light' | 'dark' | 'auto'
// 'auto' means follow the OS preference in real time.
// We store the explicit user choice so it survives page reloads.

(function () {
    const STORAGE_KEY = 'skies-theme';
    const html = document.documentElement;

    function systemPrefersDark() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    function applyTheme(choice) {
        const resolved = choice === 'auto'
            ? (systemPrefersDark() ? 'dark' : 'light')
            : choice;
        html.setAttribute('data-theme', resolved);
        // Keep the stored choice (not the resolved one) so auto re-evaluates dynamically.
        html.dataset.themeChoice = choice;
    }

    // Cycle: auto → light → dark → auto
    function nextTheme(current) {
        return { auto: 'light', light: 'dark', dark: 'auto' }[current] ?? 'auto';
    }

    function storedChoice() {
        return localStorage.getItem(STORAGE_KEY) || 'auto';
    }

    // Apply immediately to prevent flash
    applyTheme(storedChoice());

    // When the OS preference changes while theme is 'auto', re-apply
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        if (storedChoice() === 'auto') applyTheme('auto');
    });

    // Wire the button once DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
        const btn = document.getElementById('themeToggle');
        if (!btn) return;

        btn.addEventListener('click', function () {
            const current = storedChoice();
            const next = nextTheme(current);
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);

            // Visual feedback: brief press state
            btn.style.transform = 'scale(0.88)';
            setTimeout(() => { btn.style.transform = ''; }, 120);
        });
    });
})();
