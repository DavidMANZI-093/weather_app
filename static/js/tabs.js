document.addEventListener('DOMContentLoaded', function () {
    const tabs   = document.querySelectorAll('.tab[data-target]');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            const targetId = tab.dataset.target;

            tabs.forEach(function (t) {
                t.classList.toggle('active', t === tab);
                t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
            });

            panels.forEach(function (panel) {
                const isTarget = panel.id === targetId;
                panel.classList.toggle('active', isTarget);
                panel.hidden = !isTarget;
            });
        });
    });
});
