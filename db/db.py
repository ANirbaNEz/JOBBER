import sqlite3
import hashlib
import json
from typing import Optional, List, Dict
from datetime import datetime
from .schema import init_db


class JobberDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(db_path)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def is_duplicate(self, job_url: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT job_id FROM discovered_jobs WHERE url = ?', (job_url,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def add_job(self, title: str, company: str, url: str, jd: str,
                required_skills: str, app_type: str = "form", source: str = "unknown") -> int:
        if self.is_duplicate(url):
            self.audit_log("job_skipped_duplicate", None, None, "skipped", f"Duplicate job: {url}")
            return -1

        job_hash = hashlib.md5(url.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO discovered_jobs
                (title, company, url, job_description, required_skills, app_type, source, job_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, company, url, jd, required_skills, app_type, source, job_hash))
            conn.commit()
            job_id = cursor.lastrowid
            self.audit_log("job_added", job_id, None, "added", f"New job: {title} at {company}")
            return job_id
        except sqlite3.IntegrityError as e:
            self.audit_log("job_error", None, None, "error", f"Database error: {str(e)}")
            return -1
        finally:
            conn.close()

    def get_job(self, job_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM discovered_jobs WHERE job_id = ?', (job_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_jobs(self, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM discovered_jobs ORDER BY scraped_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_application(self, job_id: int, resume_path: str, cover_letter_path: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications
            (job_id, status, tailored_resume_path, cover_letter_path)
            VALUES (?, ?, ?, ?)
        ''', (job_id, "pending", resume_path, cover_letter_path))
        conn.commit()
        app_id = cursor.lastrowid
        self.audit_log("application_created", job_id, app_id, "pending", "Application created")
        conn.close()
        return app_id

    def update_application_status(self, app_id: int, status: str, notes: str = ""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE applications
            SET status = ?, submitted_at = ?
            WHERE app_id = ?
        ''', (status, datetime.now(), app_id))
        conn.commit()

        app = self.get_application(app_id)
        if app:
            self.audit_log("application_updated", app['job_id'], app_id, status, notes)
        conn.close()

    def get_application(self, app_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE app_id = ?', (app_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_applications_by_job(self, job_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE job_id = ?', (job_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def cache_form_mapping(self, job_id: int, form_fields: Dict, field_mapping: Dict):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO form_mappings
            (job_id, form_fields_json, field_mapping_json)
            VALUES (?, ?, ?)
        ''', (job_id, json.dumps(form_fields), json.dumps(field_mapping)))
        conn.commit()
        conn.close()

    def get_form_mapping(self, job_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM form_mappings WHERE job_id = ?', (job_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "form_fields": json.loads(dict(row)["form_fields_json"]),
                "field_mapping": json.loads(dict(row)["field_mapping_json"])
            }
        return None

    def cache_llm_output(self, job_id: int, tailored_resume: Dict, cover_letter: str, qa_responses: List[Dict]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO llm_cache
            (job_id, resume_tailoring, cover_letter, qa_responses)
            VALUES (?, ?, ?, ?)
        ''', (job_id, json.dumps(tailored_resume), cover_letter, json.dumps(qa_responses)))
        conn.commit()
        conn.close()

    def get_llm_cache(self, job_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM llm_cache WHERE job_id = ?', (job_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            row_dict = dict(row)
            return {
                "tailored_resume": json.loads(row_dict["resume_tailoring"]),
                "cover_letter": row_dict["cover_letter"],
                "qa_responses": json.loads(row_dict["qa_responses"])
            }
        return None

    def audit_log(self, action: str, job_id: Optional[int], app_id: Optional[int],
                  status: str, message: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log
            (action, job_id, app_id, status, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (action, job_id, app_id, status, message))
        conn.commit()
        conn.close()

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM discovered_jobs')
        total_jobs = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM applications')
        total_apps = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM applications WHERE status = "submitted"')
        submitted = cursor.fetchone()['count']

        conn.close()

        return {
            "total_jobs_discovered": total_jobs,
            "total_applications": total_apps,
            "submitted_applications": submitted,
            "pending_applications": total_apps - submitted
        }
