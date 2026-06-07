const CITIES = [
    "Tokyo", "Delhi", "Shanghai", "Sao Paulo", "Mexico City", "Cairo", "Mumbai", "Beijing", 
    "Dhaka", "Osaka", "New York", "Karachi", "Buenos Aires", "Chongqing", "Istanbul", 
    "Kolkata", "Manila", "Lagos", "Rio de Janeiro", "Tianjin", "Kinshasa", "Guangzhou", 
    "Los Angeles", "Moscow", "Shenzhen", "Lahore", "Bangalore", "Paris", "Bogota", "Jakarta", 
    "Chennai", "Lima", "Bangkok", "Seoul", "Nagoya", "Hyderabad", "London", "Tehran", 
    "Chicago", "Chengdu", "Nanjing", "Wuhan", "Ho Chi Minh City", "Luanda", "Ahmedabad", 
    "Kuala Lumpur", "Xi'an", "Hong Kong", "Dongguan", "Hangzhou", "Foshan", "Shenyang", 
    "Riyadh", "Baghdad", "Santiago", "Surat", "Madrid", "Suzhou", "Pune", "Harbin", 
    "Houston", "Dallas", "Toronto", "Dar es Salaam", "Miami", "Belo Horizonte", "Singapore", 
    "Philadelphia", "Atlanta", "Fukuoka", "Khartoum", "Barcelona", "Johannesburg", 
    "Saint Petersburg", "Qingdao", "Dalian", "Washington", "Yangon", "Alexandria", "Jinan", 
    "Guadalajara", "Kigali", "Nairobi", "Dubai", "Berlin", "Rome", "Amsterdam", "San Francisco"
];

document.addEventListener("DOMContentLoaded", () => {
    const cityInput = document.getElementById("city-input");
    const ghostInput = document.getElementById("city-input-ghost");
    const hintBtn = document.getElementById("hint-btn");

    if (!cityInput || !ghostInput || !hintBtn) return;

    let currentSuggestion = "";

    function updateGhostText() {
        const val = cityInput.value;
        if (!val) {
            ghostInput.value = "";
            currentSuggestion = "";
            hintBtn.style.display = "none";
            return;
        }

        const match = CITIES.find(c => c.toLowerCase().startsWith(val.toLowerCase()));
        if (match && match.toLowerCase() !== val.toLowerCase()) {
            const typedPart = val;
            const untypedPart = match.substring(val.length);
            ghostInput.value = typedPart + untypedPart;
            currentSuggestion = match;
            hintBtn.style.display = "inline-flex";
        } else {
            ghostInput.value = "";
            currentSuggestion = "";
            hintBtn.style.display = "none";
        }
    }

    cityInput.addEventListener("input", updateGhostText);

    function applySuggestion() {
        if (currentSuggestion) {
            cityInput.value = currentSuggestion;
            updateGhostText();
            cityInput.focus();
        }
    }

    cityInput.addEventListener("keydown", (e) => {
        if (e.key === "Tab" && currentSuggestion && currentSuggestion.toLowerCase() !== cityInput.value.toLowerCase()) {
            e.preventDefault();
            applySuggestion();
        }
    });

    hintBtn.addEventListener("click", (e) => {
        e.preventDefault();
        applySuggestion();
    });
});
