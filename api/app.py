from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config, load_master_resume
from db.db import JobberDB
from scraper.mock_scraper import MockScraper
from scraper.naukri_scraper import NaukriScraper
from scraper.internshala_scraper import InternShalaScraper
from llm_engine.mock_llm import MockLLM
from llm_engine.resume_tailor import ResumeTailor
from llm_engine.cover_letter_generator import CoverLetterGenerator
from llm_engine.qa_generator import QAGenerator
from renderer.pdf_renderer import PDFRenderer
from form_mapper.form_parser import FormParser
from form_mapper.field_mapper import FieldMapper
from logging_monitor.logger import get_logger
import os
import json

app = Flask(__name__)
CORS(app)
logger = get_logger("jobber_api")

# Initialize
config = get_config()
db = JobberDB(config.db_path)
master_resume = load_master_resume(config.master_resume_path)


# ==================== JOBS ====================

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get discovered jobs"""
    limit = request.args.get('limit', 50, type=int)
    jobs = db.get_all_jobs(limit=limit)
    return jsonify(jobs)


@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job"""
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


# ==================== SCRAPING ====================

@app.route('/api/scrape', methods=['POST'])
def scrape_jobs():
    """Scrape jobs from source"""
    data = request.json
    query = data.get('query', 'Python Developer')
    source = data.get('source', 'naukri')
    limit = data.get('limit', 10)

    try:
        if source == 'mock':
            scraper = MockScraper()
        elif source == 'naukri':
            scraper = NaukriScraper()
        elif source == 'internshala':
            scraper = InternShalaScraper()
        else:
            return jsonify({"error": "Invalid source"}), 400

        jobs = scraper.scrape(query, limit=limit)

        added = 0
        dedups = 0

        for job in jobs:
            if db.is_duplicate(job.url):
                dedups += 1
                continue

            job_id = db.add_job(
                title=job.title,
                company=job.company,
                url=job.url,
                jd=job.job_description,
                required_skills=job.required_skills,
                app_type=job.app_type,
                source=job.source
            )
            added += 1

        return jsonify({
            "added": added,
            "dedups": dedups,
            "total_scraped": len(jobs)
        })

    except Exception as e:
        logger.error(f"Scrape failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== PROCESSING ====================

@app.route('/api/process/<int:job_id>', methods=['POST'])
def process_job(job_id):
    """Process job: tailor resume + generate content"""
    try:
        job = db.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        # Use mock LLM
        llm = MockLLM()

        # Tailor resume
        tailor = ResumeTailor(llm)
        tailored = tailor.tailor(master_resume, job['job_description'])

        if not tailored:
            return jsonify({"error": "Failed to tailor resume"}), 500

        # Generate cover letter
        cover_gen = CoverLetterGenerator(llm)
        cover_letter = cover_gen.generate(master_resume, job['job_description'], job['company'])

        # Generate Q&A
        qa_gen = QAGenerator(llm)
        qa_responses = qa_gen.generate(job['job_description'], master_resume.summary or "")

        # Cache in DB
        db.cache_llm_output(job_id, tailored, cover_letter, qa_responses)

        return jsonify({
            "tailored_resume": tailored,
            "cover_letter": cover_letter,
            "qa_responses": qa_responses,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== RENDERING ====================

@app.route('/api/render/<int:job_id>', methods=['POST'])
def render_pdf(job_id):
    """Generate PDF resume"""
    try:
        job = db.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        cache = db.get_llm_cache(job_id)
        if not cache:
            return jsonify({"error": "Job not processed"}), 400

        renderer = PDFRenderer(config.generated_resumes_dir)
        tailored = cache['tailored_resume']

        pdf_path = renderer.render(tailored, job['company'], job['title'])

        if not pdf_path:
            return jsonify({"error": "Failed to render PDF"}), 500

        return jsonify({
            "pdf_path": pdf_path,
            "pdf_url": f"/api/pdf/{job_id}"
        })

    except Exception as e:
        logger.error(f"Render failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pdf/<int:job_id>', methods=['GET'])
def get_pdf(job_id):
    """Get PDF file"""
    try:
        for pdf_file in os.listdir(config.generated_resumes_dir):
            if str(job_id) in pdf_file or str(job_id) in pdf_file:
                pdf_path = os.path.join(config.generated_resumes_dir, pdf_file)
                with open(pdf_path, 'rb') as f:
                    return f.read(), 200, {'Content-Type': 'application/pdf'}

        return jsonify({"error": "PDF not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== FORM MAPPING ====================

@app.route('/api/map-form/<int:job_id>', methods=['POST'])
def map_form(job_id):
    """Map form fields to resume"""
    try:
        job = db.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        cache = db.get_llm_cache(job_id)
        if not cache:
            return jsonify({"error": "Job not processed"}), 400

        # Use mock form
        from form_mapper.mock_form import MOCK_FORM_HTML
        parser = FormParser()
        form_data = parser.parse_form_html(MOCK_FORM_HTML)

        if not form_data:
            return jsonify({"error": "Failed to parse form"}), 500

        # Map fields
        mapper = FieldMapper()
        tailored = cache['tailored_resume']
        field_mapping = mapper.map_fields(form_data['fields'], tailored)

        # Cache
        db.cache_form_mapping(job_id, form_data['fields'], field_mapping)

        return jsonify({
            "form_fields": form_data['fields'],
            "field_mapping": field_mapping,
            "captcha_detected": form_data['captcha_detected'],
            "mapped_count": len(field_mapping),
            "total_fields": len(form_data['fields'])
        })

    except Exception as e:
        logger.error(f"Map form failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== REVIEW ====================

@app.route('/api/review/<int:job_id>', methods=['GET'])
def review_job(job_id):
    """Get all data for review"""
    try:
        job = db.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        llm_cache = db.get_llm_cache(job_id)
        form_cache = db.get_form_mapping(job_id)

        return jsonify({
            "job": job,
            "tailored_resume": llm_cache['tailored_resume'] if llm_cache else None,
            "cover_letter": llm_cache['cover_letter'] if llm_cache else None,
            "qa_responses": llm_cache['qa_responses'] if llm_cache else None,
            "form_fields": form_cache['form_fields'] if form_cache else None,
            "field_mapping": form_cache['field_mapping'] if form_cache else None
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== STATUS ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get overall statistics"""
    stats = db.get_stats()
    return jsonify(stats)


# ==================== HEALTH ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "master_resume": master_resume.name,
        "db_path": config.db_path
    })


# ==================== DASHBOARD ====================

@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Serve dashboard HTML"""
    dashboard_path = Path(__file__).parent / 'dashboard.html'
    return send_file(str(dashboard_path), mimetype='text/html')


@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and save master resume"""
    try:
        resume_data = request.json

        # Validate required fields
        if not resume_data.get('name') or not resume_data.get('email'):
            return jsonify({"error": "Name and email are required"}), 400

        # Save to master_resume.json
        resume_path = Path(config.master_resume_path)
        with open(resume_path, 'w') as f:
            json.dump(resume_data, f, indent=2)

        # Reload config
        global master_resume
        master_resume = load_master_resume(str(resume_path))

        logger.info(f"Master resume updated: {resume_data.get('name')}")
        return jsonify({
            "status": "success",
            "name": resume_data.get('name'),
            "email": resume_data.get('email')
        })

    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
