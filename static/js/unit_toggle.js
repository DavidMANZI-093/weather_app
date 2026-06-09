document.addEventListener("DOMContentLoaded", () => {
    const btnCelsius = document.getElementById("btn-celsius");
    const btnFahrenheit = document.getElementById("btn-fahrenheit");
    if (!btnCelsius || !btnFahrenheit) return;

    let currentUnit = 'C';

    function setUnit(unit) {
        if (currentUnit === unit) return;
        currentUnit = unit;
        localStorage.setItem("weatherTempUnit", unit);

        if (unit === 'C') {
            btnCelsius.classList.add("active");
            btnFahrenheit.classList.remove("active");
        } else {
            btnFahrenheit.classList.add("active");
            btnCelsius.classList.remove("active");
        }

        const tempNums = document.querySelectorAll("[data-temp-c]");
        tempNums.forEach(el => {
            const celsiusVal = parseFloat(el.getAttribute("data-temp-c"));
            if (isNaN(celsiusVal)) return;

            if (unit === 'C') {
                el.textContent = celsiusVal;
            } else {
                const fahrenheitVal = (celsiusVal * 9/5) + 32;
                el.textContent = fahrenheitVal.toFixed(1).replace(/\.0$/, '');
            }
        });

        const unitChars = document.querySelectorAll(".unit-char");
        unitChars.forEach(el => {
            el.textContent = unit;
        });
    }

    btnCelsius.addEventListener("click", () => setUnit('C'));
    btnFahrenheit.addEventListener("click", () => setUnit('F'));

    const savedUnit = localStorage.getItem("weatherTempUnit");
    if (savedUnit === 'F') {
        currentUnit = ''; // force update
        setUnit('F');
    }
});
