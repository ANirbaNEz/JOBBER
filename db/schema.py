import sqlite3
from pathlib import Path


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discovered_jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            job_description TEXT,
            required_skills TEXT,
            app_type TEXT,
            source TEXT,
            job_hash TEXT UNIQUE,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            tailored_resume_path TEXT,
            cover_letter_path TEXT,
            form_data_path TEXT,
            submitted_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES discovered_jobs(job_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS form_mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            form_fields_json TEXT,
            field_mapping_json TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES discovered_jobs(job_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_cache (
            cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            resume_tailoring TEXT,
            cover_letter TEXT,
            qa_responses TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES discovered_jobs(job_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            job_id INTEGER,
            app_id INTEGER,
            status TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db("jobber.db")
    print("Database initialized successfully!")
