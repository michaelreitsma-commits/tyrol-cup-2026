import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    """Create the attempts table if it doesn't exist."""
    with get_db_connection() as conn:
        with conn.cursor() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS attempts (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    discipline TEXT NOT NULL,
                    category TEXT NOT NULL,
                    run_name TEXT,
                    date DATE NOT NULL,
                    time_seconds DOUBLE PRECISION NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL
                );
                """
            )
        conn.commit()


def determine_category(age: int, gender: str, discipline: str) -> str:
    """
    Ski categories:
    - Girls: <=16 female
    - Boys: <=16 male
    - Women 17–49, Men 17–49
    - Women 50+, Men 50+

    Snowboard categories (no age split):
    - Snowboard Women
    - Snowboard Men
    """
    g = (gender or "").strip().lower()
    d = (discipline or "").strip().lower()

    # Snowboard ignores age
    if d.startswith("snow"):
        return "Snowboard Men" if g == "male" else "Snowboard Women"

    # Ski uses age + gender
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
        date_str = (request.form.get("date") or "").strip()
        minutes_str = request.form.get("time_minutes")
        seconds_str = request.form.get("time_seconds")
        notes = request.form.get("notes", "").strip()

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
            return render_template("submit.html", error=error, today=date_str or date.today().isoformat())

        # Age
        try:
            age = int(age_str)
            if age <= 0:
                raise ValueError()
        except ValueError:
            error = "Age must be a positive whole number."
            return render_template("submit.html", error=error, today=date_str)

        # Time
        try:
            minutes = int(minutes_str)
            seconds = float(seconds_str)
            if minutes < 0 or minutes > 59 or seconds < 0 or seconds >= 60:
                raise ValueError()
            time_seconds = minutes * 60 + seconds
        except ValueError:
            error = "Enter minutes (0–59) and seconds (0–59.99)."
            return render_template("submit.html", error=error, today=date_str)

        # Date (Render + Postgres prefer DATE type)
        try:
            run_date = date.fromisoformat(date_str)
        except ValueError:
            error = "Date must be in YYYY-MM-DD format."
            return render_template("submit.html", error=error, today=date.today().isoformat())

        # Normalize gender and discipline
        gender_norm = "Male" if gender.lower().startswith("m") else "Female"
        discipline_norm = "Snowboard" if discipline.lower().startswith("snow") else "Ski"

        if not run_name:
            run_name = "Main course"

        category = determine_category(age, gender_norm, discipline_norm)
        created_at = datetime.utcnow()

        init_db()

        with get_db_connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    """
                    INSERT INTO attempts (
                        name, age, gender, discipline, category, run_name, date,
                        time_seconds, notes, created_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        name,
                        age,
                        gender_norm,
                        discipline_norm,
                        category,
                        run_name,
                        run_date,
                        time_seconds,
                        notes,
                        created_at,
                    ),
                )
            conn.commit()

        return redirect(url_for("leaderboard"))

    today = date.today().isoformat()
    return render_template("submit.html", today=today)


@app.route("/leaderboard")
def leaderboard():
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

    init_db()

    with get_db_connection() as conn:
        with conn.cursor() as c:
            for cat in categories:
                c.execute(
                    """
                    SELECT
                        name,
                        category,
                        run_name,
                        MIN(time_seconds) AS best_time
                    FROM attempts
                    WHERE category = %s
                    GROUP BY name, category, run_name
                    ORDER BY best_time ASC
                    """,
                    (cat,),
                )
                category_results[cat] = c.fetchall()

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
