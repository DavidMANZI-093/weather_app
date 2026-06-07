import os
import sqlite3
import requests
import pycountry
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, g, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_compress import Compress

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # Cache static files for 1 day
Compress(app)

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_GEO  = "https://api.openweathermap.org/geo/1.0/reverse"

DATABASE = os.path.join(app.instance_path, "weather.db")
os.makedirs(app.instance_path, exist_ok=True)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    UNIQUE NOT NULL,
            password  TEXT    NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS searches (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            query_type  TEXT    NOT NULL CHECK(query_type IN ('city', 'coords')),
            query_input TEXT    NOT NULL,
            city_name   TEXT,
            country     TEXT,
            temperature REAL,
            condition   TEXT,
            humidity    INTEGER,
            wind_speed  REAL,
            weather_icon TEXT,
            searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address  TEXT
        );
    """)

    existing = db.execute("SELECT id FROM admins WHERE username = 'admin'").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123"))
        )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please sign in to access the dashboard.", "info")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Weather API helpers
# ---------------------------------------------------------------------------

def fetch_weather_by_city(city: str):
    if not OPENWEATHER_API_KEY:
        return None, "API key not configured. Set OPENWEATHER_API_KEY."
    try:
        resp = requests.get(OPENWEATHER_BASE, params={
            "q":     city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }, timeout=8)
        if resp.status_code == 404:
            return None, f"City \"{city}\" not found. Check spelling and try again."
        if resp.status_code == 401:
            return None, "Invalid API key. Contact the administrator."
        resp.raise_for_status()
        return resp.json(), None
    except requests.Timeout:
        return None, "Weather service timed out. Please try again."
    except requests.RequestException as e:
        return None, f"Network error: {e}"


def fetch_weather_by_coords(lat: float, lon: float):
    if not OPENWEATHER_API_KEY:
        return None, "API key not configured. Set OPENWEATHER_API_KEY."
    try:
        resp = requests.get(OPENWEATHER_BASE, params={
            "lat":   lat,
            "lon":   lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }, timeout=8)
        if resp.status_code == 400:
            return None, "Invalid coordinates provided."
        if resp.status_code == 401:
            return None, "Invalid API key. Contact the administrator."
        resp.raise_for_status()
        return resp.json(), None
    except requests.Timeout:
        return None, "Weather service timed out. Please try again."
    except requests.RequestException as e:
        return None, f"Network error: {e}"


def get_flag_emoji(country_code):
    if not country_code or len(country_code) != 2:
        return ""
    return chr(ord(country_code[0].upper()) + 127397) + chr(ord(country_code[1].upper()) + 127397)

def parse_weather(data: dict) -> dict:
    country_code = data.get("sys", {}).get("country", "")
    country_name = country_code
    flag_emoji = ""
    if country_code:
        try:
            country_obj = pycountry.countries.get(alpha_2=country_code)
            if country_obj:
                country_name = country_obj.name
            flag_emoji = get_flag_emoji(country_code)
        except Exception:
            pass

    return {
        "city":        data.get("name", "Unknown"),
        "country":     country_name,
        "country_code": country_code,
        "flag_emoji":  flag_emoji,
        "temperature": round(data["main"]["temp"], 1),
        "feels_like":  round(data["main"]["feels_like"], 1),
        "temp_min":    round(data["main"]["temp_min"], 1),
        "temp_max":    round(data["main"]["temp_max"], 1),
        "condition":   data["weather"][0]["description"].title(),
        "icon":        data["weather"][0]["icon"],
        "humidity":    data["main"]["humidity"],
        "wind_speed":  round(data["wind"]["speed"] * 3.6, 1),  # m/s -> km/h
        "pressure":    data["main"].get("pressure", 0),
        "visibility":  round(data.get("visibility", 0) / 1000, 1),
        "timestamp":   datetime.utcfromtimestamp(data["dt"]).strftime("%A, %d %B %Y  %H:%M UTC"),
    }


def record_search(query_type, query_input, weather):
    db = get_db()
    db.execute("""
        INSERT INTO searches
            (query_type, query_input, city_name, country, temperature,
             condition, humidity, wind_speed, weather_icon, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        query_type,
        query_input,
        weather["city"],
        weather["country"],
        weather["temperature"],
        weather["condition"],
        weather["humidity"],
        weather["wind_speed"],
        weather["icon"],
        request.remote_addr
    ))
    db.commit()


# ---------------------------------------------------------------------------
# Guest routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    mode = request.form.get("mode", "city").strip()

    if mode == "city":
        city = request.form.get("city", "").strip()
        if not city:
            return render_template("index.html", error="Please enter a city name.")
        data, err = fetch_weather_by_city(city)
        query_input = city

    elif mode == "coords":
        lat_raw = request.form.get("latitude", "").strip()
        lon_raw = request.form.get("longitude", "").strip()
        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError
        except ValueError:
            return render_template("index.html", error="Enter valid latitude (−90 to 90) and longitude (−180 to 180).")
        data, err = fetch_weather_by_coords(lat, lon)
        query_input = f"{lat}, {lon}"

    else:
        return render_template("index.html", error="Unknown search method.")

    if err:
        return render_template("index.html", error=err)

    weather = parse_weather(data)
    record_search(mode, query_input, weather)
    return render_template("result.html", weather=weather, mode=mode, query=query_input)


@app.route("/api/weather/coords")
def api_weather_coords():
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400

    data, err = fetch_weather_by_coords(lat, lon)
    if err:
        return jsonify({"error": err}), 502

    weather = parse_weather(data)
    record_search("coords", f"{lat}, {lon}", weather)
    return jsonify(weather)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("admin_login.html", error="Both fields are required.")

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()

        if not admin or not check_password_hash(admin["password"], password):
            return render_template("admin_login.html", error="Invalid username or password.")

        session["admin_id"]   = admin["id"]
        session["admin_name"] = admin["username"]
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()

    stats = db.execute("""
        SELECT
            COUNT(*)                                        AS total_searches,
            COUNT(DISTINCT ip_address)                      AS unique_visitors,
            COUNT(CASE WHEN query_type = 'city'   THEN 1 END) AS city_searches,
            COUNT(CASE WHEN query_type = 'coords' THEN 1 END) AS coord_searches,
            COUNT(CASE WHEN date(searched_at) = date('now') THEN 1 END) AS today_searches
        FROM searches
    """).fetchone()

    top_cities = db.execute("""
        SELECT city_name, country, COUNT(*) AS count
        FROM searches
        WHERE city_name IS NOT NULL
        GROUP BY city_name, country
        ORDER BY count DESC
        LIMIT 8
    """).fetchall()

    recent = db.execute("""
        SELECT * FROM searches
        ORDER BY searched_at DESC
        LIMIT 50
    """).fetchall()

    daily_trend = db.execute("""
        SELECT date(searched_at) AS day, COUNT(*) AS count
        FROM searches
        WHERE searched_at >= date('now', '-14 days')
        GROUP BY day
        ORDER BY day
    """).fetchall()

    daily_trend_dict = [dict(row) for row in daily_trend]

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        top_cities=top_cities,
        recent=recent,
        daily_trend=daily_trend_dict
    )


@app.route("/admin/searches")
@admin_required
def admin_searches():
    db     = get_db()
    page   = max(1, request.args.get("page", 1, type=int))
    per_pg = 25
    offset = (page - 1) * per_pg

    total = db.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    rows  = db.execute(
        "SELECT * FROM searches ORDER BY searched_at DESC LIMIT ? OFFSET ?",
        (per_pg, offset)
    ).fetchall()

    return render_template(
        "admin_searches.html",
        rows=rows,
        page=page,
        total=total,
        per_page=per_pg,
        pages=max(1, (total + per_pg - 1) // per_pg)
    )


@app.route("/admin/searches/delete/<int:search_id>", methods=["POST"])
@admin_required
def delete_search(search_id):
    db = get_db()
    db.execute("DELETE FROM searches WHERE id = ?", (search_id,))
    db.commit()
    flash("Record deleted.", "success")
    return redirect(url_for("admin_searches"))


@app.route("/admin/searches/clear", methods=["POST"])
@admin_required
def clear_all_searches():
    db = get_db()
    db.execute("DELETE FROM searches")
    db.commit()
    flash("All search history cleared.", "success")
    return redirect(url_for("admin_searches"))


@app.route("/admin/username", methods=["POST"])
@admin_required
def change_username():
    new_username = request.form.get("new_username", "").strip()

    if not new_username or len(new_username) < 3:
        flash("Username must be at least 3 characters long.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    existing = db.execute("SELECT id FROM admins WHERE username = ?", (new_username,)).fetchone()
    if existing and existing["id"] != session["admin_id"]:
        flash("Username is already taken.", "error")
        return redirect(url_for("admin_dashboard"))

    db.execute("UPDATE admins SET username = ? WHERE id = ?", (new_username, session["admin_id"]))
    db.commit()
    session["admin_name"] = new_username
    flash("Username updated successfully.", "success")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/password", methods=["POST"])
@admin_required
def change_password():
    current  = request.form.get("current_password", "")
    new_pass = request.form.get("new_password", "")
    confirm  = request.form.get("confirm_password", "")

    db    = get_db()
    admin = db.execute("SELECT * FROM admins WHERE id = ?", (session["admin_id"],)).fetchone()

    if not check_password_hash(admin["password"], current):
        flash("Current password is incorrect.", "error")
    elif len(new_pass) < 6:
        flash("New password must be at least 6 characters.", "error")
    elif new_pass != confirm:
        flash("Passwords do not match.", "error")
    else:
        db.execute(
            "UPDATE admins SET password = ? WHERE id = ?",
            (generate_password_hash(new_pass), session["admin_id"])
        )
        db.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
