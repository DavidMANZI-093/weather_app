# Skies — Weather Information System

A Flask + SQLite weather app for the UNILAK HCI CAT assessment.

## Setup

```bash
pip install -r requirements.txt
```

## Configuration

Export your OpenWeatherMap API key before starting:

```bash
export OPENWEATHER_API_KEY="your_key_here"
```

Get a free key at https://openweathermap.org/api

## Run

```bash
python app.py
```

Then open http://localhost:5000

## Default admin credentials

Username: `admin`
Password: `admin123`

Change the password via the dashboard after first login.

## Project layout

```
weather_app/
├── app.py                  # All Flask routes and business logic
├── requirements.txt
├── instance/
│   └── weather.db          # SQLite database (auto-created on first run)
├── static/
│   ├── css/main.css        # Design tokens, components, responsive layout
│   └── js/
│       ├── theme.js        # System-preference detection + user override
│       ├── tabs.js         # City / coordinates tab switching
│       └── geolocation.js  # Smart geolocation with permission state handling
└── templates/
    ├── base.html           # Nav, theme toggle, flash messages, footer
    ├── index.html          # Search page (city + coords tabs, quick chips)
    ├── result.html         # Weather result card
    ├── admin_login.html    # Admin authentication
    ├── admin_dashboard.html# Stats, chart, top cities, password change
    └── admin_searches.html # Full paginated search history with delete
```

## HCI notes

- **Theme**: auto (follows OS) → light → dark, cycled by the toggle. Choice persists in localStorage.
- **Geolocation**: Checks `navigator.permissions` before prompting. Silently hides the button if the API is unavailable. Distinguishes denied vs unavailable vs timeout with specific messages.
- **Tabs**: ARIA `role="tab"` / `aria-selected` / `aria-controls` for screen readers.
- **Forms**: All inputs have associated `<label>` elements. Error messages are in `role="alert"` regions.
- **Responsive**: Tested down to 320px. Coords grid collapses to single column on small phones.
