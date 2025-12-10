# Virtual Ski Race App

A simple Flask web app for logging virtual ski race attempts and showing leaderboards
by age and gender category.

## Categories

Racers are assigned automatically to one of these categories based on age and gender:

- **Girls**: age ≤ 16, gender = Female
- **Boys**: age ≤ 16, gender = Male
- **Women 17–49**: 17 ≤ age ≤ 49, gender = Female
- **Men 17–49**: 17 ≤ age ≤ 49, gender = Male
- **Women 50+**: age ≥ 50, gender = Female
- **Men 50+**: age ≥ 50, gender = Male

Each category has its own leaderboard (best time per racer).

## Quickstart

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python app.py
   ```

4. Open your browser at:

   - `http://127.0.0.1:5000/leaderboard` to see leaderboards
   - `http://127.0.0.1:5000/submit` to log attempts

A SQLite database file (`ski_race.db`) will be created automatically in the same folder.

## Deployment

You can deploy this app to a service such as Render, Railway, or PythonAnywhere.
Typically you will:

- Push this folder to a GitHub repository.
- Create a new **Web Service** on your chosen platform.
- Point it at your repo and set the start command to:

  ```bash
  gunicorn app:app
  ```

(You may need to add `gunicorn` to `requirements.txt` for production.)
