import sqlite3
from pathlib import Path

# Paths relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "honorary_stats.db"


def get_connection() -> sqlite3.Connection:
    """
    Returns a connection to data/honorary_stats.db with row_factory
    set to sqlite3.Row for dict-like access to rows.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Builds the SQLite database schema if tables do not exist.
    Tables: job_roles, skills, courses, centres, schemes, role_schemes, skill_cards.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        -- 1. Job Roles (Tailor, Cook, Electrician)
        CREATE TABLE IF NOT EXISTS job_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_hi TEXT NOT NULL
        );

        -- 2. Skills per role (level is "current" or "next")
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            name_hi TEXT NOT NULL,
            level TEXT NOT NULL CHECK(level IN ('current', 'next')),
            FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE
        );

        -- 3. Next-level Courses per role
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            provider TEXT NOT NULL,
            duration TEXT NOT NULL,
            link TEXT NOT NULL,
            is_sample INTEGER DEFAULT 1,
            FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE
        );

        -- 4. Nearest Certification / RPL Centres per role
        CREATE TABLE IF NOT EXISTS centres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            link TEXT NOT NULL,
            is_sample INTEGER DEFAULT 1,
            FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE
        );

        -- 5. Government Schemes
        CREATE TABLE IF NOT EXISTS schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_hi TEXT NOT NULL,
            reason TEXT NOT NULL,
            link TEXT NOT NULL,
            is_sample INTEGER DEFAULT 1
        );

        -- 6. Association table: role to schemes
        CREATE TABLE IF NOT EXISTS role_schemes (
            role_id INTEGER NOT NULL,
            scheme_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, scheme_id),
            FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE,
            FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE
        );

        -- 7. Skill Cards (shared with Person C's card code)
        CREATE TABLE IF NOT EXISTS skill_cards (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            skills_json TEXT NOT NULL,
            years_experience INTEGER,
            language TEXT DEFAULT 'en',
            created_at TEXT NOT NULL,
            FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE RESTRICT
        );

        -- Useful indexes for fast lookups
        CREATE INDEX IF NOT EXISTS idx_skills_role ON skills(role_id);
        CREATE INDEX IF NOT EXISTS idx_courses_role ON courses(role_id);
        CREATE INDEX IF NOT EXISTS idx_centres_role ON centres(role_id);
        CREATE INDEX IF NOT EXISTS idx_role_schemes_role ON role_schemes(role_id);
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database schema initialized at: {DB_PATH}")
