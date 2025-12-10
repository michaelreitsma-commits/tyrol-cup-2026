# Quick Test Data Loader for Tyrol Cup 2026
# Run using:  py load_test_data.py

import sqlite3
from datetime import datetime

DATABASE = "ski_race.db"

TEST_ROWS = [
    # --- Ski categories ---
    ("Alice Girl", 12, "Female", "Ski", "Girls", "Main course", "2026-01-10", 75.50, "Test run"),
    ("Bobby Boy", 15, "Male", "Ski", "Boys", "Main course", "2026-01-11", 72.40, "Test run"),
    ("Wendy Woman", 35, "Female", "Ski", "Women 17–49", "GS", "2026-01-12", 68.20, "Test run"),
    ("Mark Man", 28, "Male", "Ski", "Men 17–49", "GS", "2026-01-12", 63.10, "Test run"),
    ("Paula Senior", 55, "Female", "Ski", "Women 50+", "Slalom", "2026-01-13", 82.90, "Test run"),
    ("Carl Senior", 60, "Male", "Ski", "Men 50+", "Slalom", "2026-01-13", 85.75, "Test run"),

    # --- Snowboard categories ---
    ("Sally Snow", 22, "Female", "Snowboard", "Snowboard Women", "SB Course", "2026-01-14", 90.00, "Test run"),
    ("Sam Snow", 30, "Male", "Snowboard", "Snowboard Men", "SB Course", "2026-01-14", 88.50, "Test run"),
]

def load_test_data():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    for row in TEST_ROWS:
        c.execute(
            """
            INSERT INTO attempts (
                name, age, gender, discipline, category, run_name, date,
                time_seconds, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*row, datetime.utcnow().isoformat(timespec="seconds"))
        )

    conn.commit()
    conn.close()
    print("\nTest data successfully loaded!\n")


if __name__ == "__main__":
    load_test_data()
    print("You can now run the app:  py app.py")
