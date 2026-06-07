// Smart geolocation handler.
// Strategy:
//   1. If the Geolocation API is absent, hide the button entirely.
//   2. If permission was previously denied, show an informative message instead
//      of attempting again (avoids a silent failure on mobile).
//   3. On first click, request position. Populate lat/lon inputs and switch
//      focus to the submit button so the user can confirm.
//   4. Handle all failure codes with user-friendly copy.

document.addEventListener('DOMContentLoaded', function () {
    const btn      = document.getElementById('geolocateBtn');
    const label    = document.getElementById('geolocateLabel');
    const hint     = document.getElementById('geoHint');
    const latInput = document.getElementById('lat-input');
    const lonInput = document.getElementById('lon-input');

    if (!btn || !latInput || !lonInput) return;

    // Hide button entirely if API unavailable (old browser, insecure origin, etc.)
    if (!('geolocation' in navigator)) {
        btn.style.display = 'none';
        return;
    }

    // Check existing permission state without prompting the user
    if (navigator.permissions) {
        navigator.permissions.query({ name: 'geolocation' }).then(function (result) {
            if (result.state === 'denied') {
                markDenied();
            }
            result.addEventListener('change', function () {
                if (result.state === 'denied') markDenied();
                else restoreButton();
            });
        });
    }

    btn.addEventListener('click', function () {
        setLoading(true);

        navigator.geolocation.getCurrentPosition(
            function onSuccess(pos) {
                const lat = pos.coords.latitude.toFixed(6);
                const lon = pos.coords.longitude.toFixed(6);

                latInput.value = lat;
                lonInput.value = lon;

                setLoading(false);
                label.textContent = 'Location detected';
                btn.classList.add('btn--secondary');
                btn.disabled = false;

                hint.textContent = '';

                // Move focus to submit so the user just presses Enter/taps
                const submit = btn.closest('form').querySelector('[type="submit"]');
                if (submit) submit.focus();
            },
            function onError(err) {
                setLoading(false);
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        markDenied();
                        break;
                    case err.POSITION_UNAVAILABLE:
                        hint.textContent = 'Location unavailable. Enter coordinates manually.';
                        break;
                    case err.TIMEOUT:
                        hint.textContent = 'Location request timed out. Try again.';
                        break;
                    default:
                        hint.textContent = 'Could not get location.';
                }
            },
            { timeout: 10000, maximumAge: 60000 }
        );
    });

    function setLoading(isLoading) {
        btn.disabled = isLoading;
        label.textContent = isLoading ? 'Detecting...' : 'Use my location';
    }

    function markDenied() {
        btn.disabled = true;
        label.textContent = 'Location blocked';
        hint.textContent = 'Enable location in your browser settings to use this.';
    }

    function restoreButton() {
        btn.disabled = false;
        label.textContent = 'Use my location';
        hint.textContent = '';
    }
});
