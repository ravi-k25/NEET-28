from datetime import date, datetime, timedelta
import random
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "neet_companion.db"

app = Flask(__name__)

SUBJECTS = ["Physics", "Chemistry", "Biology", "Other"]
PRIORITIES = ["High", "Medium", "Low"]
STATUSES = ["Pending", "In Progress", "Completed"]
TEST_STATUSES = ["Upcoming", "Completed"]
REVISION_STATUSES = ["Due", "Completed", "Snoozed"]
SYLLABUS_SEED = {
    "Biology": {
        "Human Physiology": ["Digestive System", "Respiratory System", "Circulatory System", "Excretory System"],
        "Cell Structure": ["Cell Theory", "Cell Organelles", "Biomolecules", "Transport Across Membrane"],
        "Genetics": ["Mendelian Genetics", "DNA Replication", "Mutation", "Evolution Basics"],
    },
    "Physics": {
        "Mechanics": ["Laws of Motion", "Work, Energy, Power", "Momentum", "Rotational Motion"],
        "Electricity": ["Current Electricity", "Capacitance", "Magnetism", "EMI"],
        "Optics": ["Ray Optics", "Wave Optics", "Optical Instruments", "Diffraction"],
    },
    "Chemistry": {
        "Physical Chemistry": ["Atomic Structure", "Chemical Bonding", "Thermodynamics", "Equilibrium"],
        "Organic Chemistry": ["Hydrocarbons", "Haloalkanes", "Aldehydes", "Amines"],
        "Inorganic Chemistry": ["Periodic Table", "Coordination Compounds", "Metallurgy", "P-Block Elements"],
    },
}
STUDY_TARGET_MINUTES = 8 * 60
BREAK_MESSAGES = [
    "Drink some water, dear 🥤❤️",
    "Stretch your shoulders a little 🌸",
    "Look away from the screen for 20 seconds 👀",
    "Take a small walk 🚶‍♀️",
    "Take a deep breath. You've got this 🫶",
    "Rest properly. Recovery is part of studying too ❤️",
]
TIMER_PRESETS = {
    "pomodoro": {"label": "POMODORO", "study_minutes": 25, "break_minutes": 5, "session_type": "pomodoro"},
    "standard": {"label": "STANDARD", "study_minutes": 50, "break_minutes": 10, "session_type": "standard"},
    "deep_work": {"label": "DEEP WORK", "study_minutes": 90, "break_minutes": 15, "session_type": "deep_work"},
}
COMPLETION_MESSAGES = [
    "Done! One step closer to that NEET seat 🩺❤️",
    "Another mission defeated 😤🔥",
    "Excellent work. Small wins build big futures 💪",
    "Checked off. The future you is proud of you ✨",
]
DISTRACTION_TYPES = ["Instagram", "YouTube", "Gaming", "Scrolling", "Chatting", "Other"]
ACHIEVEMENT_DEFINITIONS = [
    {"key": "first_focus_session", "title": "First Focus Session", "emoji": "🏁", "description": "Complete first study session."},
    {"key": "five_hour_day", "title": "5 Hour Day", "emoji": "⏱️", "description": "Study at least 5 hours in one day."},
    {"key": "seven_day_streak", "title": "7 Day Streak", "emoji": "🔥", "description": "Reach a 7-day streak."},
    {"key": "thirty_day_streak", "title": "30 Day Streak", "emoji": "🔥", "description": "Reach a 30-day streak."},
    {"key": "ten_chapters", "title": "10 Chapters", "emoji": "📚", "description": "Complete 10 chapters/topics."},
    {"key": "five_tests", "title": "5 Tests", "emoji": "📝", "description": "Complete 5 tests."},
    {"key": "ninety_percent_accuracy", "title": "90% Accuracy", "emoji": "🎯", "description": "Achieve 90%+ test accuracy."},
    {"key": "hundred_mistakes_reviewed", "title": "100 Mistakes Reviewed", "emoji": "🧠", "description": "Review 100 mistakes."},
]
PERSONAL_MESSAGE_MAP = {
    "morning": ["Good morning, future doctor ☀️🩺", "Morning power. One strong session first. ❤️"],
    "afternoon": ["Keep the momentum. Your future self is watching. ✨", "The afternoon is yours. Stay steady. 💪"],
    "evening": ["One more honest session and you can rest. 🌙", "Evening study counts. Keep your promise to yourself. ✨"],
    "starting_session": ["Start now. The first few minutes are the hardest. ❤️", "One focused block is enough to begin. ✨"],
    "focus": ["Stay with it. One session at a time ❤️", "Deep work wins. Trust the process. 🔥"],
    "break": ["Drink some water, dear 🥤", "Rest your eyes for a minute 👀"],
    "low_productivity": ["You planned 8 hours and completed 1h 20m. Start one focus session now.", "This is the moment to stop delaying and begin. 🚀"],
    "high_productivity": ["Strong work today. Keep the rhythm. ✨", "Your consistency is showing. Keep it up. ❤️"],
    "test_upcoming": ["Tomorrow's test is close. Review your weak topics. 📝", "Sharpen your weak spots before the test arrives."],
    "test_today": ["Today's test deserves a calm, focused review. 🧠", "Trust your prep. Keep it simple."],
    "revision_due": ["Let's refresh this before your brain forgets it 🧠", "Revision now beats panic later. 💪"],
    "mistakes_due": ["Every mistake here is one less mistake in the real exam ❤️", "Review this one before it repeats."],
    "streak": ["Another day added to the streak 🔥", "Consistency is becoming your superpower."],
    "achievement": ["🏆 NEW ACHIEVEMENT", "You are building a real habit now 🔥❤️"],
    "goal_complete": ["Today's mission complete. Go rest, you earned it ❤️", "MISSION COMPLETE. You've earned your rest."],
    "distraction": ["1h 15m lost today. Don't lose the next hour too.", "Phone away. Focus session starts now."],
}


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DATABASE_DIR.mkdir(exist_ok=True)

    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value) VALUES
                ('daily_study_target_minutes', '480'),
                ('daily_study_target_hours', '8'),
                ('completed_study_hours', '0'),
                ('streak_days', '0')
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT DEFAULT 'Other',
                chapter TEXT,
                priority TEXT DEFAULT 'Medium',
                estimated_minutes INTEGER NOT NULL,
                deadline TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_DATE,
                completed_at TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter TEXT,
                duration_minutes INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                test_date TEXT NOT NULL,
                test_time TEXT NOT NULL,
                subjects TEXT,
                syllabus TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Upcoming',
                created_at TEXT DEFAULT CURRENT_DATE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL UNIQUE,
                physics_score INTEGER DEFAULT 0,
                chemistry_score INTEGER DEFAULT 0,
                biology_score INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                attempted INTEGER DEFAULT 0,
                correct INTEGER DEFAULT 0,
                incorrect INTEGER DEFAULT 0,
                unattempted INTEGER DEFAULT 0,
                silly_mistakes INTEGER DEFAULT 0,
                conceptual_mistakes INTEGER DEFAULT 0,
                total_marks INTEGER DEFAULT 0,
                percentage REAL DEFAULT 0,
                accuracy REAL DEFAULT 0,
                attempt_rate REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_DATE,
                FOREIGN KEY (test_id) REFERENCES tests(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS syllabus_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                topic TEXT NOT NULL,
                status TEXT DEFAULT 'Not Started',
                updated_at TEXT DEFAULT CURRENT_DATE,
                UNIQUE(subject, chapter, topic)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                topic TEXT NOT NULL,
                learned_date TEXT NOT NULL,
                revision_date TEXT NOT NULL,
                revision_number INTEGER NOT NULL,
                status TEXT DEFAULT 'Due',
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_DATE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter TEXT,
                question TEXT,
                mistake_type TEXT NOT NULL,
                why_wrong TEXT,
                correct_concept TEXT,
                test_id INTEGER,
                review_date TEXT,
                status TEXT DEFAULT 'Open',
                created_at TEXT DEFAULT CURRENT_DATE,
                FOREIGN KEY (test_id) REFERENCES tests(id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS distractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_DATE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS achievement_unlocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_DATE
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value) VALUES
                ('strict_mode', '0'),
                ('preferred_study_mode', 'pomodoro'),
                ('break_message_toggle', '1'),
                ('achievement_celebration_toggle', '1'),
                ('daily_motivational_messages_toggle', '1')
            """
        )

        sync_syllabus_seed()
        connection.commit()


def get_setting(key, default=None):
    with get_db_connection() as connection:
        row = connection.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return row["value"]


def set_setting(key, value):
    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        connection.commit()


def get_strict_mode_enabled():
    value = get_setting("strict_mode", "0")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def set_strict_mode_enabled(value):
    set_setting("strict_mode", "1" if bool(value) else "0")


def format_minutes(minutes):
    total_minutes = max(int(minutes), 0)
    hours, mins = divmod(total_minutes, 60)
    return f"{hours}h {mins:02d}m"


def get_daily_study_target_minutes():
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT key, value FROM app_settings
            WHERE key IN ('daily_study_target_minutes', 'daily_study_target_hours')
            ORDER BY CASE key WHEN 'daily_study_target_minutes' THEN 0 ELSE 1 END
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return 8 * 60

    try:
        value = int(row["value"])
    except (TypeError, ValueError):
        return 8 * 60

    if row["key"] == "daily_study_target_hours":
        return max(value * 60, 0)
    return max(value, 0)


def set_daily_study_target_minutes(minutes):
    try:
        target_minutes = max(int(minutes), 0)
    except (TypeError, ValueError):
        return False

    target_hours = max(target_minutes / 60, 0)

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (key, value) VALUES ('daily_study_target_minutes', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(target_minutes),),
        )
        connection.execute(
            """
            INSERT INTO app_settings (key, value) VALUES ('daily_study_target_hours', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(target_hours),),
        )
        connection.commit()

    return True


def get_focus_session_count_for_date(target_date=None):
    target_date = target_date or date.today().isoformat()
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM study_sessions WHERE date(completed_at) = date(?)",
            (target_date,),
        ).fetchone()
    return int(row["count"]) if row else 0


def get_morning_message():
    return get_contextual_message("morning")


def get_default_message_for_time():
    hour = datetime.now().hour
    if hour < 12:
        return get_contextual_message("morning")
    if hour < 17:
        return get_contextual_message("afternoon")
    return get_contextual_message("evening")


def get_hours_and_minutes(minutes):
    total_minutes = max(int(minutes), 0)
    hours, remaining_minutes = divmod(total_minutes, 60)
    return hours, remaining_minutes


def get_today_study_summary(target_date=None):
    target_date = target_date or date.today().isoformat()
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS sessions, COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM study_sessions
            WHERE date(completed_at) = date(?)
            """,
            (target_date,),
        ).fetchone()

    total_minutes = int(row["total_minutes"]) if row else 0
    sessions = int(row["sessions"]) if row else 0
    return {"sessions": sessions, "total_minutes": total_minutes, "average_minutes": round(total_minutes / sessions, 1) if sessions else 0}


def get_weekly_totals(reference_date=None):
    reference_date = reference_date or date.today()
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    totals = {}

    for offset in range(7):
        current_day = start_of_week + timedelta(days=offset)
        current_key = current_day.isoformat()
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) = date(?)",
                (current_key,),
            ).fetchone()
        totals[current_key] = int(row["total_minutes"]) if row else 0

    return totals


def get_weekly_chart_data(reference_date=None):
    reference_date = reference_date or date.today()
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    labels = []
    values = []

    for offset in range(7):
        current_day = start_of_week + timedelta(days=offset)
        labels.append(current_day.strftime("%a"))
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) = date(?)",
                (current_day.isoformat(),),
            ).fetchone()
        values.append(int(row["total_minutes"]) if row else 0)

    return {"labels": labels, "values": values}


def get_subject_breakdown():
    all_subjects = ["Physics", "Chemistry", "Biology", "Other"]
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT subject, COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions GROUP BY subject"
        ).fetchall()

    totals = {row["subject"]: int(row["total_minutes"]) for row in rows}
    grand_total = sum(totals.values())

    breakdown = []
    for subject in all_subjects:
        minutes = totals.get(subject, 0)
        percentage = round((minutes / grand_total) * 100, 1) if grand_total else 0
        breakdown.append({"label": subject, "minutes": minutes, "percentage": percentage})

    ordered = sorted(
        [{"label": key, "minutes": value, "percentage": round((value / grand_total) * 100, 1) if grand_total else 0} for key, value in totals.items() if key not in all_subjects],
        key=lambda item: item["minutes"],
        reverse=True,
    )

    for item in ordered:
        if not any(entry["label"] == item["label"] for entry in breakdown):
            breakdown.append(item)

    return breakdown


def get_trend_data(days=7):
    end_date = date.today()
    labels = []
    values = []

    for offset in range(days - 1, -1, -1):
        current_day = end_date - timedelta(days=offset)
        labels.append(current_day.strftime("%b %d"))
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) = date(?)",
                (current_day.isoformat(),),
            ).fetchone()
        values.append(int(row["total_minutes"]) if row else 0)

    return {"labels": labels, "values": values}


def get_best_day_record():
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT date(completed_at) AS day, SUM(duration_minutes) AS total_minutes
            FROM study_sessions
            GROUP BY date(completed_at)
            ORDER BY total_minutes DESC, day DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None

    total_minutes = int(row["total_minutes"])
    day_value = row["day"]
    day_name = datetime.strptime(day_value, "%Y-%m-%d").strftime("%A")
    return {"day": day_name, "total_minutes": total_minutes, "date": day_value}


def get_average_daily_study_minutes():
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(DISTINCT date(completed_at)) AS active_days, COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions"
        ).fetchone()

    active_days = int(row["active_days"]) if row else 0
    total_minutes = int(row["total_minutes"]) if row else 0
    return round(total_minutes / active_days, 1) if active_days else 0


def get_total_focus_sessions():
    with get_db_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM study_sessions").fetchone()
    return int(row["count"]) if row else 0


def get_total_study_minutes():
    with get_db_connection() as connection:
        row = connection.execute("SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions").fetchone()
    return int(row["total_minutes"]) if row else 0


def get_longest_session_minutes():
    with get_db_connection() as connection:
        row = connection.execute("SELECT MAX(duration_minutes) AS longest_minutes FROM study_sessions").fetchone()
    return int(row["longest_minutes"]) if row else 0


def get_streaks_for_target(target_minutes):
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT date(completed_at) AS day, SUM(duration_minutes) AS total_minutes FROM study_sessions GROUP BY date(completed_at)"
        ).fetchall()

    totals = {row["day"]: int(row["total_minutes"]) for row in rows}
    today = date.today()
    current_streak = 0
    cursor = today
    while True:
        day_key = cursor.isoformat()
        if totals.get(day_key, 0) >= target_minutes:
            current_streak += 1
            cursor -= timedelta(days=1)
            continue
        break

    longest_streak = 0
    running_streak = 0
    if totals:
        earliest_day = min(date.fromisoformat(day) for day in totals)
        latest_day = max(date.fromisoformat(day) for day in totals)
        cursor = earliest_day
        while cursor <= latest_day:
            if totals.get(cursor.isoformat(), 0) >= target_minutes:
                running_streak += 1
                longest_streak = max(longest_streak, running_streak)
            else:
                running_streak = 0
            cursor += timedelta(days=1)

    return {"current": current_streak, "longest": longest_streak}


def get_weekly_comparison():
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    previous_week_start = current_week_start - timedelta(days=7)
    previous_week_end = current_week_start - timedelta(days=1)

    with get_db_connection() as connection:
        current_total = int(
            connection.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) BETWEEN date(?) AND date(?)",
                (current_week_start.isoformat(), (current_week_start + timedelta(days=6)).isoformat()),
            ).fetchone()["total_minutes"]
        )
        previous_total = int(
            connection.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) BETWEEN date(?) AND date(?)",
                (previous_week_start.isoformat(), previous_week_end.isoformat()),
            ).fetchone()["total_minutes"]
        )

    if previous_total <= 0:
        return {"current_minutes": current_total, "previous_minutes": previous_total, "percent_change": None, "label": "Not enough data for comparison yet."}

    percent_change = round(((current_total - previous_total) / previous_total) * 100, 1)
    sign = "+" if percent_change >= 0 else "+"
    return {
        "current_minutes": current_total,
        "previous_minutes": previous_total,
        "percent_change": percent_change,
        "label": f"{sign}{abs(percent_change)}%",
    }


def build_analytics_insights():
    target_minutes = get_daily_study_target_minutes()
    total_sessions = get_total_focus_sessions()
    if total_sessions == 0:
        return []

    subject_breakdown = get_subject_breakdown()
    best_day = get_best_day_record()
    average_session = get_average_daily_study_minutes()
    weekly_totals = get_weekly_totals()
    week_total_minutes = sum(weekly_totals.values())
    current_day_name = date.today().strftime("%A")

    insights = []

    if weekly_totals:
        highest_day = max(weekly_totals.items(), key=lambda item: item[1])
        if highest_day[1] > 0:
            day_label = datetime.strptime(highest_day[0], "%Y-%m-%d").strftime("%A")
            insights.append(f"You studied the most on {day_label} this week.")

    if subject_breakdown:
        dominant_subject = max(subject_breakdown, key=lambda item: item["minutes"])
        if dominant_subject["minutes"] > 0:
            insights.append(f"{dominant_subject['label']} accounts for {dominant_subject['percentage']}% of your study time.")

    if total_sessions > 0:
        average_session_minutes = sum(item["minutes"] for item in get_subject_breakdown()) / total_sessions
        insights.append(f"Your average focus session is {round(average_session_minutes, 0)} minutes.")

    if best_day is not None:
        insights.append(f"Your personal best day is {best_day['day']} with {format_minutes(best_day['total_minutes'])}.")

    comparison = get_weekly_comparison()
    if comparison["percent_change"] is not None:
        insights.append(f"Your study time changed by {comparison['label']} compared with last week.")

    return insights[:4]


def get_analytics_dashboard_payload():
    target_minutes = get_daily_study_target_minutes()
    today_summary = get_today_study_summary()
    target_hours = round(target_minutes / 60, 1)
    today_minutes = today_summary["total_minutes"]
    remaining_minutes = max(target_minutes - today_minutes, 0)
    progress = min(int((today_minutes / target_minutes) * 100), 100) if target_minutes else 0
    total_sessions = get_total_focus_sessions()
    total_study_minutes = get_total_study_minutes()
    average_session_length = round(total_study_minutes / total_sessions, 1) if total_sessions else 0
    weekly_chart = get_weekly_chart_data()

    return {
        "target_minutes": target_minutes,
        "target_hours": target_hours,
        "today_minutes": today_minutes,
        "remaining_minutes": remaining_minutes,
        "progress": progress,
        "sessions_today": today_summary["sessions"],
        "average_session_minutes": today_summary["average_minutes"],
        "focus_sessions_total": total_sessions,
        "average_session_length": average_session_length,
        "status_message": "🎯 Today's mission complete!" if progress >= 100 else "Keep going. One focused session at a time ❤️",
        "weekly_chart": weekly_chart,
        "subject_breakdown": get_subject_breakdown(),
        "trend_7": get_trend_data(7),
        "trend_30": get_trend_data(30),
        "best_day": get_best_day_record(),
        "current_week": get_weekly_comparison(),
        "streaks": get_streaks_for_target(target_minutes),
        "insights": build_analytics_insights(),
        "today_label": date.today().strftime("%A"),
    }


def get_today_distraction_summary():
    today = date.today().isoformat()
    with get_db_connection() as connection:
        total_minutes = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM distractions WHERE date(created_at) = date(?)",
            (today,),
        ).fetchone()["total"]
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM distractions WHERE date(created_at) = date(?)",
            (today,),
        ).fetchone()["count"]
        most_common = connection.execute(
            "SELECT type, COUNT(*) AS count, SUM(duration_minutes) AS duration FROM distractions WHERE date(created_at) = date(?) GROUP BY type ORDER BY duration DESC, count DESC LIMIT 1",
            (today,),
        ).fetchone()
    return {
        "total_minutes": int(total_minutes),
        "count": int(count),
        "most_common": dict(most_common) if most_common else None,
    }


def get_weekly_distraction_summary():
    start = date.today() - timedelta(days=date.today().weekday())
    end = start + timedelta(days=6)
    with get_db_connection() as connection:
        total = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM distractions WHERE date(created_at) BETWEEN date(?) AND date(?)",
            (start.isoformat(), end.isoformat()),
        ).fetchone()["total"]
        type_row = connection.execute(
            "SELECT type, SUM(duration_minutes) AS total FROM distractions WHERE date(created_at) BETWEEN date(?) AND date(?) GROUP BY type ORDER BY total DESC LIMIT 1",
            (start.isoformat(), end.isoformat()),
        ).fetchone()
    return {"total_minutes": int(total), "most_common": dict(type_row) if type_row else None}


def get_productivity_score():
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    total_task_count = get_task_summary()["total_tasks"]
    completed_task_count = get_task_summary()["completed_count"]
    revision_total = 0
    revision_completed = 0
    with get_db_connection() as connection:
        revision_total = int(connection.execute("SELECT COUNT(*) FROM revisions WHERE date(revision_date) = date('now')").fetchone()[0] or 0)
        revision_completed = int(connection.execute("SELECT COUNT(*) FROM revisions WHERE status = 'Completed' AND date(completed_at) = date('now')").fetchone()[0] or 0)
    distraction_summary = get_today_distraction_summary()
    distraction_minutes = distraction_summary["total_minutes"]

    study_completion = min((studied_minutes / target_minutes) * 100, 100) if target_minutes else 0
    task_completion = (completed_task_count / total_task_count * 100) if total_task_count else 100
    revision_completion = (revision_completed / revision_total * 100) if revision_total else 100
    distraction_control = max(100 - min(distraction_minutes, 180), 0)

    # Formula: 60% study target + 20% task completion + 10% revision completion + 10% distraction control.
    raw_score = (study_completion * 0.60) + (task_completion * 0.20) + (revision_completion * 0.10) + (distraction_control * 0.10)
    score = round(max(0, min(raw_score, 100)))

    if score >= 80:
        explanation = "Strong study time, but distraction was slightly high today."
    elif score >= 60:
        explanation = "Solid effort. A few extra focused blocks would lift the day higher."
    elif score >= 40:
        explanation = "You are moving, but the next session matters most."
    else:
        explanation = "The day is still recoverable. Start one focus block now."

    return {
        "score": score,
        "study_completion": round(study_completion, 1),
        "task_completion": round(task_completion, 1),
        "revision_completion": round(revision_completion, 1),
        "distraction_control": distraction_control,
        "explanation": explanation,
    }


def get_streak_summary():
    target_minutes = get_daily_study_target_minutes()
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT date(completed_at) AS day, SUM(duration_minutes) AS total_minutes FROM study_sessions GROUP BY date(completed_at)"
        ).fetchall()

    totals = {row["day"]: int(row["total_minutes"]) for row in rows}
    productive_days = [day for day, total in totals.items() if total >= target_minutes]
    today = date.today()
    current_streak = 0
    cursor = today
    while True:
        key = cursor.isoformat()
        if totals.get(key, 0) >= target_minutes:
            current_streak += 1
            cursor -= timedelta(days=1)
        else:
            break

    longest_streak = 0
    running = 0
    days_in_range = sorted({date.fromisoformat(day) for day in totals})
    if days_in_range:
        earliest = min(days_in_range)
        latest = max(days_in_range)
        cursor = earliest
        while cursor <= latest:
            key = cursor.isoformat()
            if totals.get(key, 0) >= target_minutes:
                running += 1
                longest_streak = max(longest_streak, running)
            else:
                running = 0
            cursor += timedelta(days=1)

    return {
        "current": current_streak,
        "longest": longest_streak,
        "productive_days": len(productive_days),
        "total_study_days": len(totals),
        "target_minutes": target_minutes,
    }


def unlock_achievement(key, title):
    with get_db_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO achievement_unlocks (key, title, unlocked_at) VALUES (?, ?, date('now'))",
            (key, title),
        )
        connection.commit()


def get_unlocked_achievements():
    with get_db_connection() as connection:
        rows = connection.execute("SELECT key, title, unlocked_at FROM achievement_unlocks ORDER BY unlocked_at DESC").fetchall()
    return [dict(row) for row in rows]


def refresh_achievements():
    target_minutes = get_daily_study_target_minutes()
    streak = get_streak_summary()
    with get_db_connection() as connection:
        total_focus_sessions = int(connection.execute("SELECT COUNT(*) FROM study_sessions").fetchone()[0] or 0)
        completed_chapters = int(connection.execute("SELECT COUNT(*) FROM syllabus_progress WHERE status = 'Completed'").fetchone()[0] or 0)
        completed_tests = int(connection.execute("SELECT COUNT(*) FROM tests WHERE status = 'Completed'").fetchone()[0] or 0)
        reviewed_mistakes = int(connection.execute("SELECT COUNT(*) FROM mistakes WHERE status = 'Reviewed'").fetchone()[0] or 0)
        best_accuracy = connection.execute("SELECT MAX(percentage) AS best FROM test_results").fetchone()["best"]
        best_accuracy = float(best_accuracy or 0)
        five_hour_days = int(connection.execute("SELECT COUNT(*) FROM (SELECT date(completed_at) AS day, SUM(duration_minutes) AS total FROM study_sessions GROUP BY date(completed_at)) WHERE total >= 300").fetchone()[0] or 0)

    if total_focus_sessions >= 1:
        unlock_achievement("first_focus_session", "First Focus Session")
    if five_hour_days >= 1:
        unlock_achievement("five_hour_day", "5 Hour Day")
    if streak["current"] >= 7:
        unlock_achievement("seven_day_streak", "7 Day Streak")
    if streak["current"] >= 30:
        unlock_achievement("thirty_day_streak", "30 Day Streak")
    if completed_chapters >= 10:
        unlock_achievement("ten_chapters", "10 Chapters")
    if completed_tests >= 5:
        unlock_achievement("five_tests", "5 Tests")
    if best_accuracy >= 90:
        unlock_achievement("ninety_percent_accuracy", "90% Accuracy")
    if reviewed_mistakes >= 100:
        unlock_achievement("hundred_mistakes_reviewed", "100 Mistakes Reviewed")

    return get_unlocked_achievements()


def get_contextual_message(category, context=None):
    messages = PERSONAL_MESSAGE_MAP.get(category, ["Keep going. One step at a time. ❤️"])
    return random.choice(messages)


def generate_strict_mode_message():
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    distraction_minutes = get_today_distraction_summary()["total_minutes"]
    task_summary = get_task_summary()
    overdue_count = task_summary["overdue_count"]
    remaining_minutes = max(target_minutes - studied_minutes, 0)
    if studied_minutes < target_minutes * 0.35:
        return f"You planned {format_minutes(target_minutes)} and completed {format_minutes(studied_minutes)}. Start one focus session now."
    if overdue_count >= 2:
        return "Several tasks are overdue. Stop postponing and handle the most important one first."
    if distraction_minutes > studied_minutes:
        return "Your distraction time is higher than your study time today. Phone away. Focus session starts now."
    if remaining_minutes <= 60:
        return "You're close. One more focused session and today's mission is done."
    if studied_minutes >= target_minutes:
        return "MISSION COMPLETE. You've earned your rest."
    return "Stay honest. One focused block is enough to move this day forward."


def generate_normal_mode_message():
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    if studied_minutes >= target_minutes:
        return "Today's mission complete. Go rest, you earned it ❤️"
    if studied_minutes < target_minutes * 0.35:
        return "A gentle start is still a start. Begin with one calm focus session. 💛"
    if get_today_distraction_summary()["total_minutes"] > 45:
        return "Your attention is slipping a little. Reset and protect your next session. ✨"
    return "You are doing better than you think. Keep the rhythm going. ❤️"


def get_settings_payload():
    return {
        "strict_mode": get_strict_mode_enabled(),
        "preferred_study_mode": get_setting("preferred_study_mode", "pomodoro"),
        "break_message_toggle": get_setting("break_message_toggle", "1") not in {"0", "false", "False", "no", "off"},
        "achievement_celebration_toggle": get_setting("achievement_celebration_toggle", "1") not in {"0", "false", "False", "no", "off"},
        "daily_motivational_messages_toggle": get_setting("daily_motivational_messages_toggle", "1") not in {"0", "false", "False", "no", "off"},
    }


def get_next_action_recommendation():
    task_summary = get_task_summary()
    revision_due = get_due_revisions(limit=1)
    next_test = get_next_test()
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    if revision_due:
        return f"🔁 Complete your {revision_due[0]['subject']} revision."
    if task_summary["overdue_count"] > 0:
        return "🎯 Finish one overdue high-priority task before anything else."
    if studied_minutes < target_minutes * 0.6:
        return "🔥 Start a 50-minute focus session."
    if next_test and next_test["test_date"] == date.today().isoformat():
        return "📝 Review your weak topics for today's test."
    if next_test:
        next_test_date = datetime.strptime(next_test["test_date"], "%Y-%m-%d").date()
        if (next_test_date - date.today()).days <= 1:
            return "📝 Review your weak topics for tomorrow's test."
    if task_summary["pending_count"] > 0:
        return "🎯 Finish your highest-priority task next."
    return "❤️ Everything is done. Rest properly."


def get_daily_review():
    today = date.today().isoformat()
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    completed_tasks = get_task_summary()["completed_count"]
    total_tasks = get_task_summary()["total_tasks"]
    completed_revisions = int(get_db_connection().execute("SELECT COUNT(*) FROM revisions WHERE status = 'Completed' AND date(completed_at) = date('now')").fetchone()[0] or 0)
    total_revisions = int(get_db_connection().execute("SELECT COUNT(*) FROM revisions WHERE date(revision_date) = date('now')").fetchone()[0] or 0)
    completed_tests = int(get_db_connection().execute("SELECT COUNT(*) FROM tests WHERE status = 'Completed' AND date(test_date) = date('now')").fetchone()[0] or 0)
    distraction_minutes = get_today_distraction_summary()["total_minutes"]
    score = get_productivity_score()["score"]
    streak = get_streak_summary()["current"]

    if studied_minutes <= 0 and total_tasks == 0 and total_revisions == 0 and completed_tests == 0 and distraction_minutes == 0:
        return None

    return {
        "study_minutes": studied_minutes,
        "tasks": f"{completed_tasks}/{total_tasks}",
        "revisions": f"{completed_revisions}/{total_revisions}",
        "tests": f"{completed_tests}",
        "distraction_minutes": distraction_minutes,
        "productivity": score,
        "streak": streak,
        "message": "Not a perfect day. A productive one. That's what matters. ❤️",
    }


def sync_syllabus_seed():
    with get_db_connection() as connection:
        for subject, chapters in SYLLABUS_SEED.items():
            for chapter, topics in chapters.items():
                for topic in topics:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO syllabus_progress (subject, chapter, topic, status, updated_at)
                        VALUES (?, ?, ?, 'Not Started', date('now'))
                        """,
                        (subject, chapter, topic),
                    )
        connection.commit()


def get_syllabus_progress_for_view():
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM syllabus_progress
            ORDER BY subject, chapter, topic
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_syllabus_summary():
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM syllabus_progress").fetchone()["count"]
        completed = connection.execute("SELECT COUNT(*) AS count FROM syllabus_progress WHERE status = 'Completed'").fetchone()["count"]
        in_progress = connection.execute("SELECT COUNT(*) AS count FROM syllabus_progress WHERE status = 'In Progress'").fetchone()["count"]
        not_started = connection.execute("SELECT COUNT(*) AS count FROM syllabus_progress WHERE status = 'Not Started'").fetchone()["count"]
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_rate": round((completed / total) * 100, 1) if total else 0,
    }


def get_next_test():
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM tests
            WHERE date(test_date) >= date('now')
            ORDER BY date(test_date) ASC, test_time ASC
            LIMIT 1
            """
        ).fetchone()
    return dict(row) if row is not None else None


def get_tests_for_view():
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM tests
            ORDER BY date(test_date) ASC, test_time ASC
            """
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        result = connection.execute("SELECT * FROM test_results WHERE test_id = ?", (row["id"],)).fetchone()
        item["result"] = dict(result) if result is not None else None
        items.append(item)
    return items


def get_test_summary():
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM tests").fetchone()["count"]
        upcoming = connection.execute("SELECT COUNT(*) AS count FROM tests WHERE status = 'Upcoming'").fetchone()["count"]
        completed = connection.execute("SELECT COUNT(*) AS count FROM tests WHERE status = 'Completed'").fetchone()["count"]
    return {"total": total, "upcoming": upcoming, "completed": completed}


def get_due_revisions(limit=3):
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM revisions
            WHERE status != 'Completed'
            ORDER BY date(revision_date) ASC, revision_number DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_revision_summary():
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM revisions").fetchone()["count"]
        due = connection.execute("SELECT COUNT(*) AS count FROM revisions WHERE status = 'Due'").fetchone()["count"]
        snoozed = connection.execute("SELECT COUNT(*) AS count FROM revisions WHERE status = 'Snoozed'").fetchone()["count"]
        completed = connection.execute("SELECT COUNT(*) AS count FROM revisions WHERE status = 'Completed'").fetchone()["count"]
    return {"total": total, "due": due, "snoozed": snoozed, "completed": completed}


def get_mistakes_for_view():
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM mistakes ORDER BY date(created_at) DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_mistake_summary():
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM mistakes").fetchone()["count"]
        open_count = connection.execute("SELECT COUNT(*) AS count FROM mistakes WHERE status = 'Open'").fetchone()["count"]
        reviewed = connection.execute("SELECT COUNT(*) AS count FROM mistakes WHERE status = 'Reviewed'").fetchone()["count"]
    return {"total": total, "open": open_count, "reviewed": reviewed}


def normalize_task(task_row):
    if task_row is None:
        return None

    return {
        "id": task_row["id"],
        "title": task_row["title"],
        "subject": task_row["subject"],
        "chapter": task_row["chapter"],
        "priority": task_row["priority"],
        "estimated_minutes": task_row["estimated_minutes"],
        "deadline": task_row["deadline"],
        "status": task_row["status"],
        "created_at": task_row["created_at"],
        "completed_at": task_row["completed_at"],
        "deadline_display": task_row["deadline"],
    }


def fetch_tasks_for_view(status_filter="All", subject_filter="All", priority_filter="All", sort_by="deadline"):
    query = "SELECT * FROM tasks WHERE 1 = 1"
    params = []

    if status_filter == "Today":
        query += " AND (date(created_at) = date('now') OR date(deadline) = date('now'))"
    elif status_filter == "Overdue":
        query += " AND status != 'Completed' AND deadline IS NOT NULL AND date(deadline) < date('now')"
    elif status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    if subject_filter != "All":
        query += " AND subject = ?"
        params.append(subject_filter)

    if priority_filter != "All":
        query += " AND priority = ?"
        params.append(priority_filter)

    sort_map = {
        "deadline": "ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline ASC, created_at DESC",
        "priority": "ORDER BY CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, deadline ASC",
        "estimated_minutes": "ORDER BY estimated_minutes DESC, created_at DESC",
        "created_at": "ORDER BY created_at DESC",
    }

    query += " " + sort_map.get(sort_by, sort_map["deadline"])

    with get_db_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [normalize_task(row) for row in rows]


def get_overdue_count():
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count FROM tasks
            WHERE status != 'Completed'
              AND deadline IS NOT NULL
              AND date(deadline) < date('now')
            """
        ).fetchone()
    return row["count"] if row else 0


def get_dashboard_tasks(limit=4):
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM tasks
            WHERE status != 'Completed'
              AND (date(created_at) = date('now') OR date(deadline) = date('now'))
            ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline ASC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [normalize_task(row) for row in rows]


def get_today_study_minutes():
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM study_sessions WHERE date(completed_at) = date('now')"
        ).fetchone()
    return int(row["total"]) if row else 0


def get_task_summary():
    with get_db_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM tasks").fetchone()["count"]
        completed = connection.execute("SELECT COUNT(*) AS count FROM tasks WHERE status = 'Completed'").fetchone()["count"]
        pending = connection.execute("SELECT COUNT(*) AS count FROM tasks WHERE status != 'Completed'").fetchone()["count"]
        overdue = get_overdue_count()

    remaining = max(total - completed, 0)
    completion_rate = (completed / total * 100) if total else 0

    return {
        "total_tasks": total,
        "completed_count": completed,
        "pending_count": pending,
        "remaining_count": remaining,
        "overdue_count": overdue,
        "completion_rate": round(completion_rate, 1),
    }


def parse_deadline(value):
    if value is None or value == "":
        return None

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        return parsed.isoformat()
    except ValueError:
        raise ValueError("Deadline must be in YYYY-MM-DD format.")


init_db()


@app.route("/")
def dashboard():
    target_minutes = get_daily_study_target_minutes()
    studied_minutes = get_today_study_minutes()
    remaining_minutes = max(target_minutes - studied_minutes, 0)
    progress = min(int((studied_minutes / target_minutes) * 100), 100) if target_minutes else 0
    focus_sessions = get_focus_session_count_for_date()
    with get_db_connection() as connection:
        streak_days = int(connection.execute("SELECT value FROM app_settings WHERE key = 'streak_days'").fetchone()["value"]) if connection.execute("SELECT value FROM app_settings WHERE key = 'streak_days'").fetchone() else 0
    overdue_count = get_overdue_count()
    today_tasks = get_dashboard_tasks(limit=4)
    habit = get_streak_summary()
    productivity = get_productivity_score()
    distraction_summary = get_today_distraction_summary()
    achievements = refresh_achievements()
    strict_mode = get_strict_mode_enabled()
    motivational_message = generate_strict_mode_message() if strict_mode else generate_normal_mode_message()
    next_action = get_next_action_recommendation()

    upcoming_test = get_next_test()
    revision_due = get_due_revisions(limit=3)
    syllabus_summary = get_syllabus_summary()

    return render_template(
        "dashboard.html",
        greeting="Good Morning, Future Doctor 🩺❤️",
        target_hours=target_minutes // 60,
        target_minutes=target_minutes,
        studied_minutes=studied_minutes,
        remaining_minutes=remaining_minutes,
        studied_display=format_minutes(studied_minutes),
        remaining_display=format_minutes(remaining_minutes),
        progress=progress,
        focus_sessions=focus_sessions,
        streak_days=habit["current"],
        strict_mode=strict_mode,
        productivity_score=productivity["score"],
        productivity_explanation=productivity["explanation"],
        distraction_minutes=distraction_summary["total_minutes"],
        achievement_count=len(achievements),
        motivational_message=motivational_message,
        next_action=next_action,
        today_tasks=today_tasks,
        overdue_count=overdue_count,
        upcoming_test=upcoming_test,
        revision_due=revision_due,
        syllabus_summary=syllabus_summary,
        page_name="dashboard",
    )


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        strict_mode = request.form.get("strict_mode") == "on"
        preferred_study_mode = request.form.get("preferred_study_mode", "pomodoro")
        break_message_toggle = request.form.get("break_message_toggle") == "on"
        achievement_celebration_toggle = request.form.get("achievement_celebration_toggle") == "on"
        daily_motivational_messages_toggle = request.form.get("daily_motivational_messages_toggle") == "on"

        if preferred_study_mode not in TIMER_PRESETS:
            preferred_study_mode = "pomodoro"

        set_strict_mode_enabled(strict_mode)
        set_setting("preferred_study_mode", preferred_study_mode)
        set_setting("break_message_toggle", "1" if break_message_toggle else "0")
        set_setting("achievement_celebration_toggle", "1" if achievement_celebration_toggle else "0")
        set_setting("daily_motivational_messages_toggle", "1" if daily_motivational_messages_toggle else "0")
        return redirect(url_for("settings_page", message="Settings updated ✅"))

    settings = get_settings_payload()
    return render_template(
        "settings.html",
        settings=settings,
        timer_presets=TIMER_PRESETS,
        page_name="settings",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
    )


@app.route("/distractions/add", methods=["POST"])
def add_distraction():
    distraction_type = (request.form.get("type") or "Other").strip()
    if distraction_type not in DISTRACTION_TYPES:
        distraction_type = "Other"

    try:
        duration_minutes = int(request.form.get("duration_minutes") or 0)
    except (TypeError, ValueError):
        return redirect(url_for("dashboard", error="Distraction time must be a valid number of minutes."))

    if duration_minutes <= 0:
        return redirect(url_for("dashboard", error="Distraction time must be greater than zero."))

    note = (request.form.get("note") or "").strip()
    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO distractions (type, duration_minutes, note, created_at) VALUES (?, ?, ?, date('now'))",
            (distraction_type, duration_minutes, note or None),
        )
        connection.commit()

    return redirect(url_for("dashboard", message="Distraction logged. Reset and refocus now ✨"))


@app.route("/tests")
def tests_page():
    tests = get_tests_for_view()
    summary = get_test_summary()
    next_test = get_next_test()
    return render_template(
        "tests.html",
        tests=tests,
        summary=summary,
        next_test=next_test,
        page_name="tests",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
        today=date.today().isoformat(),
    )


@app.route("/tests/add", methods=["POST"])
def add_test():
    name = (request.form.get("test_name") or "").strip()
    test_date = (request.form.get("test_date") or "").strip()
    test_time = (request.form.get("test_time") or "09:00").strip()
    subjects = (request.form.get("subjects") or "Physics, Chemistry, Biology").strip()
    syllabus = (request.form.get("syllabus") or "").strip()
    notes = (request.form.get("notes") or "").strip()
    status = request.form.get("status", "Upcoming")

    if not name or not test_date:
        return redirect(url_for("tests_page", error="Test name and date are required."))

    try:
        datetime.strptime(test_date, "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("tests_page", error="Test date must be in YYYY-MM-DD format."))

    if status not in TEST_STATUSES:
        status = "Upcoming"

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO tests (test_name, test_date, test_time, subjects, syllabus, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))
            """,
            (name, test_date, test_time, subjects, syllabus or None, notes or None, status),
        )
        connection.commit()

    return redirect(url_for("tests_page", message="Test scheduled successfully ✅"))


@app.route("/tests/<int:test_id>/result", methods=["POST"])
def save_test_result(test_id):
    try:
        physics = int(request.form.get("physics_score") or 0)
        chemistry = int(request.form.get("chemistry_score") or 0)
        biology = int(request.form.get("biology_score") or 0)
        attempted = int(request.form.get("attempted") or 0)
        correct = int(request.form.get("correct") or 0)
        incorrect = int(request.form.get("incorrect") or 0)
        unattempted = int(request.form.get("unattempted") or 0)
        silly_mistakes = int(request.form.get("silly_mistakes") or 0)
        conceptual_mistakes = int(request.form.get("conceptual_mistakes") or 0)
        total_marks = int(request.form.get("total_marks") or 0)
    except ValueError:
        return redirect(url_for("tests_page", error="All result fields must be valid numbers."))

    total_score = physics + chemistry + biology
    if total_marks <= 0:
        total_marks = max(total_score, 0)
    if attempted <= 0:
        attempted = correct + incorrect
    if unattempted <= 0:
        unattempted = max(total_marks - attempted, 0)

    percentage = round((total_score / total_marks) * 100, 1) if total_marks else 0
    accuracy = round((correct / attempted) * 100, 1) if attempted else 0
    attempt_rate = round((attempted / total_marks) * 100, 1) if total_marks else 0

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO test_results (
                test_id, physics_score, chemistry_score, biology_score, total_score, attempted,
                correct, incorrect, unattempted, silly_mistakes, conceptual_mistakes, total_marks,
                percentage, accuracy, attempt_rate, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))
            ON CONFLICT(test_id) DO UPDATE SET
                physics_score = excluded.physics_score,
                chemistry_score = excluded.chemistry_score,
                biology_score = excluded.biology_score,
                total_score = excluded.total_score,
                attempted = excluded.attempted,
                correct = excluded.correct,
                incorrect = excluded.incorrect,
                unattempted = excluded.unattempted,
                silly_mistakes = excluded.silly_mistakes,
                conceptual_mistakes = excluded.conceptual_mistakes,
                total_marks = excluded.total_marks,
                percentage = excluded.percentage,
                accuracy = excluded.accuracy,
                attempt_rate = excluded.attempt_rate
            """,
            (
                test_id,
                physics,
                chemistry,
                biology,
                total_score,
                attempted,
                correct,
                incorrect,
                unattempted,
                silly_mistakes,
                conceptual_mistakes,
                total_marks,
                percentage,
                accuracy,
                attempt_rate,
            ),
        )
        connection.execute(
            "UPDATE tests SET status = 'Completed' WHERE id = ?",
            (test_id,),
        )
        connection.commit()

    return redirect(url_for("tests_page", message="Test result saved successfully 🎯"))


@app.route("/syllabus")
def syllabus_page():
    syllabus_rows = get_syllabus_progress_for_view()
    summary = get_syllabus_summary()
    return render_template(
        "syllabus.html",
        syllabus_rows=syllabus_rows,
        summary=summary,
        page_name="syllabus",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
    )


@app.route("/syllabus/<string:subject>/<string:chapter>/<string:topic>/status", methods=["POST"])
def update_syllabus_status(subject, chapter, topic):
    new_status = request.form.get("status", "Not Started")
    valid_statuses = ["Not Started", "In Progress", "Completed"]
    if new_status not in valid_statuses:
        return redirect(url_for("syllabus_page", error="Invalid syllabus status."))

    with get_db_connection() as connection:
        connection.execute(
            "UPDATE syllabus_progress SET status = ?, updated_at = date('now') WHERE subject = ? AND chapter = ? AND topic = ?",
            (new_status, subject, chapter, topic),
        )
        connection.commit()

    return redirect(url_for("syllabus_page", message="Syllabus progress updated ✅"))


@app.route("/revisions")
def revisions_page():
    rows = []
    with get_db_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM revisions ORDER BY date(revision_date) ASC, subject ASC, chapter ASC"
        ).fetchall()
    summary = get_revision_summary()
    return render_template(
        "revisions.html",
        revisions=[dict(row) for row in rows],
        summary=summary,
        page_name="revisions",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
        today=date.today().isoformat(),
    )


@app.route("/revisions/add", methods=["POST"])
def add_revision():
    subject = request.form.get("subject", "Biology")
    chapter = (request.form.get("chapter") or "").strip()
    topic = (request.form.get("topic") or "").strip()
    learned_date = (request.form.get("learned_date") or date.today().isoformat()).strip()
    revision_date = (request.form.get("revision_date") or date.today().isoformat()).strip()
    revision_number = int(request.form.get("revision_number") or 1)

    if not chapter or not topic:
        return redirect(url_for("revisions_page", error="Chapter and topic are required."))

    try:
        datetime.strptime(learned_date, "%Y-%m-%d")
        datetime.strptime(revision_date, "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("revisions_page", error="Dates must be in YYYY-MM-DD format."))

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO revisions (subject, chapter, topic, learned_date, revision_date, revision_number, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Due', date('now'))
            """,
            (subject, chapter, topic, learned_date, revision_date, revision_number),
        )
        connection.commit()

    return redirect(url_for("revisions_page", message="Revision scheduled ✨"))


@app.route("/revisions/<int:revision_id>/status", methods=["POST"])
def update_revision_status(revision_id):
    new_status = request.form.get("status", "Due")
    if new_status not in REVISION_STATUSES:
        return redirect(url_for("revisions_page", error="Invalid revision status."))

    completed_at = date.today().isoformat() if new_status == "Completed" else None
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE revisions SET status = ?, completed_at = ? WHERE id = ?",
            (new_status, completed_at, revision_id),
        )
        connection.commit()

    return redirect(url_for("revisions_page", message="Revision updated ✅"))


@app.route("/mistakes")
def mistakes_page():
    mistakes = get_mistakes_for_view()
    summary = get_mistake_summary()
    return render_template(
        "mistakes.html",
        mistakes=mistakes,
        summary=summary,
        subjects=SUBJECTS,
        page_name="mistakes",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
        today=date.today().isoformat(),
    )


@app.route("/mistakes/add", methods=["POST"])
def add_mistake():
    subject = request.form.get("subject", "Biology")
    chapter = (request.form.get("chapter") or "").strip()
    question = (request.form.get("question") or "").strip()
    mistake_type = (request.form.get("mistake_type") or "Conceptual").strip()
    why_wrong = (request.form.get("why_wrong") or "").strip()
    correct_concept = (request.form.get("correct_concept") or "").strip()
    review_date = (request.form.get("review_date") or date.today().isoformat()).strip()

    if not question:
        return redirect(url_for("mistakes_page", error="Question description is required."))

    try:
        datetime.strptime(review_date, "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("mistakes_page", error="Review date must be in YYYY-MM-DD format."))

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO mistakes (subject, chapter, question, mistake_type, why_wrong, correct_concept, review_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', date('now'))
            """,
            (subject, chapter or None, question, mistake_type, why_wrong or None, correct_concept or None, review_date),
        )
        connection.commit()

    return redirect(url_for("mistakes_page", message="Mistake saved to your book 🧠"))


@app.route("/mistakes/<int:mistake_id>/status", methods=["POST"])
def update_mistake_status(mistake_id):
    new_status = request.form.get("status", "Open")
    allowed_statuses = ["Open", "Reviewed", "Repeated"]
    if new_status not in allowed_statuses:
        return redirect(url_for("mistakes_page", error="Invalid mistake status."))

    with get_db_connection() as connection:
        connection.execute("UPDATE mistakes SET status = ? WHERE id = ?", (new_status, mistake_id))
        connection.commit()

    return redirect(url_for("mistakes_page", message="Mistake marked updated ✨"))


@app.route("/mistakes/<int:mistake_id>/delete", methods=["POST"])
def delete_mistake(mistake_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM mistakes WHERE id = ?", (mistake_id,))
        connection.commit()
    return redirect(url_for("mistakes_page", message="Mistake removed from your book."))


@app.route("/analytics")
def analytics_page():
    target_minutes = get_daily_study_target_minutes()
    today_summary = get_today_study_summary()
    today_minutes = today_summary["total_minutes"]
    remaining_minutes = max(target_minutes - today_minutes, 0)
    progress = min(int((today_minutes / target_minutes) * 100), 100) if target_minutes else 0
    weekly_chart = get_weekly_chart_data()
    subject_breakdown = get_subject_breakdown()
    trend_7 = get_trend_data(7)
    trend_30 = get_trend_data(30)
    best_day = get_best_day_record()
    total_sessions = get_total_focus_sessions()
    total_study_minutes = get_total_study_minutes()
    longest_session = get_longest_session_minutes()
    streaks = get_streaks_for_target(target_minutes)
    weekly_comparison = get_weekly_comparison()
    insights = build_analytics_insights()
    month_start = date.today().replace(day=1)
    month_end = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    month_total_minutes = 0
    with get_db_connection() as connection:
        month_row = connection.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes FROM study_sessions WHERE date(completed_at) BETWEEN date(?) AND date(?)",
            (month_start.isoformat(), month_end.isoformat()),
        ).fetchone()
        month_total_minutes = int(month_row["total_minutes"]) if month_row else 0

    if total_sessions:
        average_session_length = round(total_study_minutes / total_sessions, 1)
    else:
        average_session_length = 0

    return render_template(
        "analytics.html",
        target_minutes=target_minutes,
        target_hours=target_minutes // 60,
        target_display=format_minutes(target_minutes),
        studied_display=format_minutes(today_minutes),
        remaining_display=format_minutes(remaining_minutes),
        progress=progress,
        status_message="🎯 Today's mission complete!" if progress >= 100 else "Keep going. One focused session at a time ❤️",
        focus_sessions_today=today_summary["sessions"],
        average_session_today=today_summary["average_minutes"],
        weekly_chart=weekly_chart,
        subject_breakdown=subject_breakdown,
        trend_7=trend_7,
        trend_30=trend_30,
        best_day=best_day,
        total_focus_sessions=total_sessions,
        total_study_hours=format_minutes(total_study_minutes),
        average_session_length=average_session_length,
        longest_session=format_minutes(longest_session),
        current_streak=streaks["current"],
        longest_streak=streaks["longest"],
        weekly_comparison=weekly_comparison,
        insights=insights,
        month_total_minutes=month_total_minutes,
        page_name="analytics",
        success_message=request.args.get("message"),
    )


@app.route("/analytics/target", methods=["POST"])
def update_daily_target():
    selected_target = request.form.get("target")
    custom_target = (request.form.get("custom_target") or "").strip()

    if custom_target:
        try:
            target_minutes = int(float(custom_target) * 60)
        except ValueError:
            return redirect(url_for("analytics_page", message="Custom study target must be a valid number of hours."))
    else:
        try:
            target_minutes = int(selected_target)
        except (TypeError, ValueError):
            target_minutes = 480

    if custom_target:
        if target_minutes <= 0:
            return redirect(url_for("analytics_page", message="Custom target must be above zero."))
    else:
        allowed_targets = {360, 420, 480, 540, 600}
        target_minutes = int(target_minutes)
        if target_minutes not in allowed_targets:
            target_minutes = 480

    set_daily_study_target_minutes(target_minutes)
    return redirect(url_for("analytics_page", message="Daily study target updated ✅"))


@app.route("/tasks")
def tasks_page():
    status_filter = request.args.get("status", "All")
    subject_filter = request.args.get("subject", "All")
    priority_filter = request.args.get("priority", "All")
    sort_by = request.args.get("sort", "deadline")
    tasks = fetch_tasks_for_view(status_filter, subject_filter, priority_filter, sort_by)
    summary = get_task_summary()

    return render_template(
        "tasks.html",
        tasks=tasks,
        subjects=SUBJECTS,
        priorities=PRIORITIES,
        statuses=["All", "Today", "Pending", "In Progress", "Completed", "Overdue"],
        selected_status=status_filter,
        selected_subject=subject_filter,
        selected_priority=priority_filter,
        selected_sort=sort_by,
        summary=summary,
        overdue_count=summary["overdue_count"],
        page_name="tasks",
        success_message=request.args.get("message"),
        error_message=request.args.get("error"),
        today=date.today().isoformat(),
    )


@app.route("/tasks/add", methods=["POST"])
def add_task():
    title = (request.form.get("title") or "").strip()
    subject = request.form.get("subject", "Other")
    chapter = (request.form.get("chapter") or "").strip()
    priority = request.form.get("priority", "Medium")
    status = request.form.get("status", "Pending")
    deadline = request.form.get("deadline")
    estimated_minutes_raw = request.form.get("estimated_minutes")

    if not title:
        return redirect(url_for("tasks_page", error="Task title is required."))

    try:
        estimated_minutes = int(estimated_minutes_raw)
    except (TypeError, ValueError):
        return redirect(url_for("tasks_page", error="Estimated study time must be a valid positive number."))

    if estimated_minutes <= 0:
        return redirect(url_for("tasks_page", error="Estimated study time must be a valid positive number."))

    if subject not in SUBJECTS:
        subject = "Other"
    if priority not in PRIORITIES:
        priority = "Medium"
    if status not in STATUSES:
        status = "Pending"

    try:
        parsed_deadline = parse_deadline(deadline)
    except ValueError:
        return redirect(url_for("tasks_page", error="Deadline must be in YYYY-MM-DD format."))

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO tasks (
                title, subject, chapter, priority, estimated_minutes, deadline, status, created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), ?)
            """,
            (title, subject, chapter or None, priority, estimated_minutes, parsed_deadline, status, None if status != "Completed" else date.today().isoformat()),
        )
        connection.commit()

    return redirect(
        url_for(
            "tasks_page",
            message="Mission added 🎯 Let's get it done, future doctor ❤️",
        )
    )


@app.route("/tasks/<int:task_id>/status", methods=["POST"]) 
def update_task_status(task_id):
    task_id = int(task_id)
    new_status = request.form.get("status", "Pending")
    if new_status not in STATUSES:
        return redirect(url_for("tasks_page", error="Invalid task status."))

    with get_db_connection() as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return redirect(url_for("tasks_page", error="Task not found."))

        completed_at = date.today().isoformat() if new_status == "Completed" else None
        connection.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (new_status, completed_at, task_id),
        )
        connection.commit()

    if new_status == "Completed":
        message = random.choice(COMPLETION_MESSAGES)
    else:
        message = f"Task moved to {new_status}."

    return redirect(url_for("tasks_page", message=message))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"]) 
def delete_task(task_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

    return redirect(url_for("tasks_page", message="Mission removed. Fresh start, future doctor 💪"))


@app.route("/tasks/<int:task_id>/edit", methods=["POST"]) 
def edit_task(task_id):
    title = (request.form.get("title") or "").strip()
    if not title:
        return redirect(url_for("tasks_page", error="Task title is required."))

    subject = request.form.get("subject", "Other")
    chapter = (request.form.get("chapter") or "").strip()
    priority = request.form.get("priority", "Medium")
    status = request.form.get("status", "Pending")
    deadline = request.form.get("deadline")
    estimated_minutes_raw = request.form.get("estimated_minutes")

    try:
        estimated_minutes = int(estimated_minutes_raw)
    except (TypeError, ValueError):
        return redirect(url_for("tasks_page", error="Estimated study time must be a valid positive number."))

    if estimated_minutes <= 0:
        return redirect(url_for("tasks_page", error="Estimated study time must be a valid positive number."))

    if subject not in SUBJECTS:
        subject = "Other"
    if priority not in PRIORITIES:
        priority = "Medium"
    if status not in STATUSES:
        status = "Pending"

    try:
        parsed_deadline = parse_deadline(deadline)
    except ValueError:
        return redirect(url_for("tasks_page", error="Deadline must be in YYYY-MM-DD format."))

    completed_at = date.today().isoformat() if status == "Completed" else None

    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET title = ?, subject = ?, chapter = ?, priority = ?, estimated_minutes = ?,
                deadline = ?, status = ?, completed_at = ?
            WHERE id = ?
            """,
            (title, subject, chapter or None, priority, estimated_minutes, parsed_deadline, status, completed_at, task_id),
        )
        connection.commit()

    return redirect(url_for("tasks_page", message="Mission updated. Keep that momentum going ✨"))


@app.route("/timer")
def timer_page():
    today_minutes = get_today_study_minutes()
    target_minutes = get_daily_study_target_minutes()
    remaining_minutes = max(target_minutes - today_minutes, 0)
    progress = min(int((today_minutes / target_minutes) * 100), 100) if target_minutes else 0

    return render_template(
        "timer.html",
        subjects=SUBJECTS,
        today_study_display=format_minutes(today_minutes),
        target_display=format_minutes(target_minutes),
        remaining_display=format_minutes(remaining_minutes),
        progress=progress,
        mode_presets=TIMER_PRESETS,
        page_name="timer",
    )


@app.route("/timer/session", methods=["POST"])
def save_completed_session():
    payload = request.get_json(silent=True) or request.form.to_dict()

    subject = payload.get("subject", "Other")
    if subject not in SUBJECTS:
        subject = "Other"

    chapter = (payload.get("chapter") or "").strip()
    duration_minutes = payload.get("duration_minutes")
    session_type = payload.get("session_type", "custom")

    try:
        duration_minutes = int(duration_minutes)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid duration."}), 400

    if duration_minutes <= 0:
        return jsonify({"ok": False, "error": "Duration must be positive."}), 400

    if session_type not in {"pomodoro", "standard", "deep_work", "custom"}:
        session_type = "custom"

    started_at = payload.get("started_at") or datetime.utcnow().isoformat(timespec="seconds")
    completed_at = payload.get("completed_at") or datetime.utcnow().isoformat(timespec="seconds")

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO study_sessions (subject, chapter, duration_minutes, session_type, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (subject, chapter or None, duration_minutes, session_type, started_at, completed_at),
        )
        connection.commit()

    return jsonify({"ok": True, "message": "Focus session saved."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
