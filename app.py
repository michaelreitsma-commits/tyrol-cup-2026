from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import os

DATABASE = "ski_race.db"

app = Flask(__name__)


def init_db():
    """Create the attempts table if it doesn't exist."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                discipline TEXT NOT NULL,
                category TEXT NOT NULL,
                run_name TEXT,
                date TEXT NOT NULL,
                time_seconds REAL NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def determine_category(age: int, gender: str, discipline: str) -> str:
    """
    Determine race category based on age, gender, and discipline.

    Ski categories:
    - Boys:        age <= 16, gender = Male
    - Girls:       age <= 16, gender = Female
    - Men 17–49:   17 <= age <= 49, gender = Male
    - Women 17–49: 17 <= age <= 49, gender = Female
    - Men 50+:     age >= 50, gender = Male
    - Women 50+:   age >= 50, gender = Female

    Snowboard categories (no age split):
    - Snowboard Men
    - Snowboard Women
    """
    g = gender.lower()
    d = discipline.lower()

    # Snowboard – ignore age
    if d.startswith("snow"):
        return "Snowboard Men" if g == "male" else "Snowboard Women"

    # Ski – use age and gender
    if age <= 16:
        return "Boys" if g == "male" else "Girls"
    elif 17 <= age <= 49:
        return "Men 17–49" if g == "male" else "Women 17–49"
    else:
        return "Men 50+" if g == "male" else "Women 50+"


@app.route("/")
def home():
    return redirect(url_for("leaderboard"))


@app.route("/submit", methods=["GET", "POST"])
def submit_attempt():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age_str = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        discipline = request.form.get("discipline", "").strip()
        run_name = request.form.get("run_name", "").strip()
        date_str = request.form.get("date")
        minutes_str = request.form.get("time_minutes")
        seconds_str = request.form.get("time_seconds")
        notes = request.form.get("notes", "").strip()

        # Basic validation
        if (
            not name
            or not age_str
            or not gender
            or not discipline
            or not date_str
            or minutes_str is None
            or seconds_str is None
        ):
            error = "Name, age, gender, discipline, date, and time are required."
            return render_template("submit.html", error=error, today=date_str)

        # Age
        try:
            age = int(age_str)
            if age <= 0:
                raise ValueError()
        except ValueError:
            error = "Age must be a positive whole number."
            return render_template("submit.html", error=error, today=date_str)

        # Minutes + seconds -> total seconds
        try:
            minutes = int(minutes_str)
            seconds = float(seconds_str)
            if minutes < 0 or minutes > 59 or seconds < 0 or seconds >= 60:
                raise ValueError()
            time_seconds = minutes * 60 + seconds
        except ValueError:
            error = "Enter minutes (0–59) and seconds (0–59.99)."
            return render_template("submit.html", error=error, today=date_str)

        # Normalize gender to "Male"/"Female"
        gender_norm = "Male" if gender.lower().startswith("m") else "Female"
        # Normalize discipline to "Ski" / "Snowboard"
        discipline_norm = "Snowboard" if discipline.lower().startswith("snow") else "Ski"

        # Default: if no run name provided, call it "Main course"
        if not run_name:
            run_name = "Main course"

        category = determine_category(age, gender_norm, discipline_norm)
        created_at = datetime.utcnow().isoformat(timespec="seconds")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO attempts (
                    name, age, gender, discipline, category, run_name, date,
                    time_seconds, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    age,
                    gender_norm,
                    discipline_norm,
                    category,
                    run_name,
                    date_str,
                    time_seconds,
                    notes,
                    created_at,
                ),
            )
            conn.commit()

        return redirect(url_for("leaderboard"))

    # GET request
    today = datetime.now().date().isoformat()
    return render_template("submit.html", today=today)


@app.route("/leaderboard")
def leaderboard():
    """Show separate leaderboards by category plus all attempts."""
    categories = [
        "Girls",
        "Boys",
        "Women 17–49",
        "Men 17–49",
        "Women 50+",
        "Men 50+",
        "Snowboard Women",
        "Snowboard Men",
    ]

    category_results = {}

    with get_db_connection() as conn:
        c = conn.cursor()

        # Best time per racer within each category
        for cat in categories:
            c.execute(
                """
                SELECT name,
                       category,
                       run_name,
                       MIN(time_seconds) AS best_time
                FROM attempts
                WHERE category = ?
                GROUP BY name, category, run_name
                ORDER BY best_time ASC
                """,
                (cat,),
            )
            category_results[cat] = c.fetchall()

        # All attempts
        c.execute(
            """
            SELECT *
            FROM attempts
            ORDER BY date ASC, time_seconds ASC
            """
        )
        all_attempts = c.fetchall()

    return render_template(
        "leaderboard.html",
        categories=categories,
        category_results=category_results,
        all_attempts=all_attempts,
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
