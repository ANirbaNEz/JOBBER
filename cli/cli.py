import click
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config, load_master_resume, validate_master_resume
from db.db import JobberDB
from logging_monitor.logger import setup_logger
from scraper.indeed_scraper import IndeedScraper
from scraper.mock_scraper import MockScraper
from llm_engine.llm_client import GeminiClient
from llm_engine.mock_llm import MockLLM
from llm_engine.resume_tailor import ResumeTailor
from llm_engine.cover_letter_generator import CoverLetterGenerator
from llm_engine.qa_generator import QAGenerator
from renderer.pdf_renderer import PDFRenderer
from form_mapper.form_parser import FormParser
from form_mapper.field_mapper import FieldMapper
from form_mapper.form_cache import FormCache
from form_mapper.mock_form import MOCK_FORM_HTML
from executor.browser_executor import BrowserExecutor
from executor.email_executor import EmailExecutor
from cli.review_ui import (
    print_job_header, print_resume_section, print_cover_letter,
    print_qa_responses, print_form_mapping, prompt_review_approval,
    print_submission_result, print_summary
)
import json


logger = setup_logger("jobber", "./logs/jobber.log")


@click.group()
def cli():
    """Job Application Agent - Semi-autonomous job application assistant"""
    pass


@cli.command()
def init():
    """Initialize the application with master resume and database"""
    try:
        logger.info("Initializing Jobber...")

        config = get_config()
        logger.info(f"Configuration loaded from .env")

        master_resume = load_master_resume(config.master_resume_path)
        logger.info(f"Master resume loaded: {master_resume.name}")

        if not validate_master_resume(master_resume):
            logger.error("Master resume validation failed. Please check all required fields.")
            raise ValueError("Invalid master resume format")

        logger.info("Master resume validated successfully")

        db = JobberDB(config.db_path)
        logger.info(f"Database initialized at {config.db_path}")

        Path(config.generated_resumes_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Generated resumes directory created at {config.generated_resumes_dir}")

        logger.info("✓ Initialization complete!")
        logger.info(f"  - Name: {master_resume.name}")
        logger.info(f"  - Email: {master_resume.email}")
        logger.info(f"  - Skills: {len(master_resume.skills)} skills")
        logger.info(f"  - Database: {config.db_path}")

    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
def status():
    """Show application statistics"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)
        stats = db.get_stats()

        click.echo("\n=== Application Statistics ===")
        click.echo(f"Total Jobs Discovered: {stats['total_jobs_discovered']}")
        click.echo(f"Total Applications: {stats['total_applications']}")
        click.echo(f"Submitted: {stats['submitted_applications']}")
        click.echo(f"Pending: {stats['pending_applications']}")
        click.echo()

    except Exception as e:
        logger.error(f"Failed to fetch status: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--limit', default=10, help='Number of recent jobs to show')
def jobs(limit):
    """List recently discovered jobs"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)
        jobs_list = db.get_all_jobs(limit=limit)

        if not jobs_list:
            click.echo("No jobs found in database")
            return

        click.echo(f"\n=== Recent Jobs ({len(jobs_list)}) ===\n")
        for job in jobs_list:
            click.echo(f"[{job['job_id']}] {job['title']} at {job['company']}")
            click.echo(f"    URL: {job['url']}")
            click.echo(f"    Type: {job['app_type']} | Source: {job['source']}")
            click.echo()

    except Exception as e:
        logger.error(f"Failed to fetch jobs: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
def logs():
    """Show recent audit logs"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)
        audit_logs = db.get_audit_log(limit=20)

        click.echo(f"\n=== Recent Audit Logs ({len(audit_logs)}) ===\n")
        for log in audit_logs:
            click.echo(f"[{log['timestamp']}] {log['action'].upper()}: {log['message']}")

    except Exception as e:
        logger.error(f"Failed to fetch logs: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--query', prompt='Job search query', help='e.g., "Python Engineer", "Data Scientist"')
@click.option('--location', default='', help='Job location (optional)')
@click.option('--limit', default=10, help='Number of jobs to scrape')
@click.option('--source', default='mock', type=click.Choice(['mock', 'indeed']), help='Job source')
def scrape(query, location, limit, source):
    """Scrape jobs from job boards"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)

        click.echo(f"\n=== Scraping {source.upper()} for '{query}' ===\n")

        if source == 'mock':
            scraper = MockScraper()
            jobs = scraper.scrape(query, location=location, limit=limit)
        elif source == 'indeed':
            scraper = IndeedScraper()
            jobs = scraper.scrape(query, location=location, limit=limit)

        if not jobs:
            click.echo("No jobs found.")
            return

        dedups = 0
        added = 0

        for job in jobs:
            if db.is_duplicate(job.url):
                dedups += 1
                logger.info(f"Duplicate: {job.title}")
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
            click.echo(f"[{job_id}] {job.title} @ {job.company}")
            click.echo(f"    {job.url}\n")

        click.echo(f"\n=== Scrape Complete ===")
        click.echo(f"Added: {added} | Duplicates: {dedups} | Total scraped: {len(jobs)}")

    except Exception as e:
        logger.error(f"Scrape failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.argument('job_id', type=int)
def process(job_id):
    """Process a job: tailor resume, generate cover letter and Q&A"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)
        master_resume = load_master_resume(config.master_resume_path)

        job = db.get_job(job_id)
        if not job:
            raise click.ClickException(f"Job {job_id} not found")

        click.echo(f"\n=== Processing Job {job_id} ===")
        click.echo(f"Title: {job['title']}")
        click.echo(f"Company: {job['company']}\n")

        click.echo("(Using mock LLM for testing - provide valid GEMINI_API_KEY in .env for real responses)")
        llm = MockLLM()

        click.echo("Tailoring resume...")
        tailor = ResumeTailor(llm)
        tailored = tailor.tailor(master_resume, job['job_description'])

        if not tailored:
            raise click.ClickException("Failed to tailor resume")

        click.echo(f"  Selected skills: {', '.join(tailored['skills'][:5])}...")

        click.echo("Generating cover letter...")
        cover_gen = CoverLetterGenerator(llm)
        cover_letter = cover_gen.generate(master_resume, job['job_description'], job['company'])

        if not cover_letter:
            raise click.ClickException("Failed to generate cover letter")

        click.echo(f"  Generated {len(cover_letter)} chars")

        click.echo("Generating Q&A responses...")
        qa_gen = QAGenerator(llm)
        qa_responses = qa_gen.generate(job['job_description'], master_resume.summary or "")

        if not qa_responses:
            raise click.ClickException("Failed to generate Q&A")

        click.echo(f"  Generated {len(qa_responses)} Q&A pairs")

        db.cache_llm_output(job_id, tailored, cover_letter, qa_responses)

        click.echo("\n=== Processing Complete ===")
        click.echo(f"Resume tailored with {len(tailored['skills'])} skills")
        click.echo(f"Cover letter generated ({len(cover_letter)} chars)")
        click.echo(f"Q&A responses generated ({len(qa_responses)} questions)")
        click.echo(f"\nUse: python cli.py render {job_id}  # to generate PDF resume")

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.argument('job_id', type=int)
def render(job_id):
    """Generate PDF resume from processed job"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)

        job = db.get_job(job_id)
        if not job:
            raise click.ClickException(f"Job {job_id} not found")

        cache = db.get_llm_cache(job_id)
        if not cache:
            raise click.ClickException(f"Job {job_id} not processed. Run: python cli.py process {job_id}")

        click.echo(f"\n=== Rendering PDF for Job {job_id} ===")
        click.echo(f"Title: {job['title']}")
        click.echo(f"Company: {job['company']}\n")

        renderer = PDFRenderer(config.generated_resumes_dir)
        tailored = cache['tailored_resume']

        pdf_path = renderer.render(tailored, job['company'], job['title'])

        if not pdf_path:
            raise click.ClickException("Failed to render PDF")

        click.echo(f"PDF generated: {pdf_path}")
        click.echo(f"Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        click.echo(f"\nUse: python cli.py map-form {job_id}  # to parse and map application form")

    except Exception as e:
        logger.error(f"PDF rendering failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command('map-form')
@click.argument('job_id', type=int)
@click.option('--url', default='', help='Application form URL (optional)')
def map_form(job_id, url):
    """Parse form and map resume data to form fields"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)

        job = db.get_job(job_id)
        if not job:
            raise click.ClickException(f"Job {job_id} not found")

        cache_obj = db.get_form_mapping(job_id)
        if cache_obj:
            click.echo(f"Form already cached for job {job_id}")
            click.echo(f"Fields: {len(cache_obj['form_fields'])} | Mapped: {len(cache_obj['field_mapping'])}")
            return

        cache = db.get_llm_cache(job_id)
        if not cache:
            raise click.ClickException(f"Job {job_id} not processed. Run: python cli.py process {job_id}")

        click.echo(f"\n=== Mapping Form for Job {job_id} ===")
        click.echo(f"Title: {job['title']}")
        click.echo(f"Company: {job['company']}\n")

        parser = FormParser()
        mapper = FieldMapper()

        if url:
            click.echo(f"Parsing form from URL: {url}")
            form_data = parser.parse_form_url(url)
        else:
            click.echo("Using mock form for testing")
            form_data = parser.parse_form_html(MOCK_FORM_HTML)

        if not form_data:
            raise click.ClickException("Failed to parse form")

        click.echo(f"Parsed {form_data['field_count']} form fields")
        click.echo(f"Required fields: {form_data['required_count']}")
        click.echo(f"CAPTCHA detected: {form_data['captcha_detected']}\n")

        tailored = cache['tailored_resume']
        field_mapping = mapper.map_fields(form_data['fields'], tailored)

        click.echo(f"Mapped {len(field_mapping)}/{form_data['field_count']} fields:\n")
        for field_name, value in list(field_mapping.items())[:5]:
            preview = value[:40] + "..." if len(value) > 40 else value
            click.echo(f"  {field_name}: {preview}")

        if len(field_mapping) > 5:
            click.echo(f"  ... and {len(field_mapping) - 5} more")

        db.cache_form_mapping(job_id, form_data['fields'], field_mapping)

        click.echo(f"\nForm mapping cached for job {job_id}")
        click.echo(f"Use: python cli.py submit {job_id}  # to fill form and submit")

    except Exception as e:
        logger.error(f"Form mapping failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.argument('job_id', type=int)
@click.option('--headless', is_flag=True, default=True, help='Run browser in headless mode')
def submit(job_id, headless):
    """Fill form and submit application"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)

        job = db.get_job(job_id)
        if not job:
            raise click.ClickException(f"Job {job_id} not found")

        form_cache = db.get_form_mapping(job_id)
        if not form_cache:
            raise click.ClickException(f"Job {job_id} not form-mapped. Run: python cli.py map-form {job_id}")

        llm_cache = db.get_llm_cache(job_id)
        if not llm_cache:
            raise click.ClickException(f"Job {job_id} not processed. Run: python cli.py process {job_id}")

        click.echo(f"\n=== Submitting Job {job_id} ===")
        click.echo(f"Title: {job['title']}")
        click.echo(f"Company: {job['company']}")
        click.echo(f"URL: {job['url']}\n")

        field_mapping = form_cache['field_mapping']
        pdf_path = None

        for job_pdf in os.listdir(config.generated_resumes_dir):
            if str(job_id) in job_pdf or job['company'].replace(" ", "") in job_pdf:
                pdf_path = os.path.join(config.generated_resumes_dir, job_pdf)
                break

        if not pdf_path:
            click.echo("Warning: No PDF resume found. Will attempt to fill text fields only.")

        if job['app_type'] == 'email':
            click.echo("Application type: EMAIL")
            app_email = job.get('company_email', '')
            if not app_email:
                raise click.ClickException("Company email not found in job details")

            executor = EmailExecutor(
                config.smtp_server,
                config.smtp_port,
                config.smtp_email,
                config.smtp_password
            )

            subject = f"Application: {job['title']} at {job['company']}"
            body = llm_cache['cover_letter']

            if executor.execute(app_email, subject, body, pdf_path):
                click.echo(f"Successfully sent email to {app_email}")
                db.update_application_status(job_id, "submitted", "Email sent via SMTP")
            else:
                raise click.ClickException(f"Failed to send email: {executor.error_message}")

        else:
            click.echo("Application type: FORM (Browser)")
            executor = BrowserExecutor(headless=headless, timeout=config.browser_timeout)

            if executor.execute(job['url'], field_mapping, pdf_path):
                click.echo("Successfully submitted application")
                db.update_application_status(job_id, "submitted", "Form submitted via browser")
            else:
                error = executor.error_message
                if error == "CAPTCHA_REQUIRES_USER_INTERVENTION":
                    click.echo("CAPTCHA detected - user intervention required")
                    db.update_application_status(job_id, "captcha_required", "User must solve CAPTCHA and submit manually")
                    raise click.ClickException(error)
                else:
                    raise click.ClickException(f"Failed to submit: {error}")

        click.echo(f"\nApplication status: SUBMITTED")
        click.echo(f"Timestamp: {db.get_application(job_id)['submitted_at']}")

    except Exception as e:
        logger.error(f"Submission failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.argument('job_id', type=int)
def review(job_id):
    """Review all content before submission (HITL approval)"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)

        job = db.get_job(job_id)
        if not job:
            raise click.ClickException(f"Job {job_id} not found")

        llm_cache = db.get_llm_cache(job_id)
        if not llm_cache:
            raise click.ClickException(f"Job {job_id} not processed. Run: python cli.py process {job_id}")

        form_cache = db.get_form_mapping(job_id)
        if not form_cache:
            raise click.ClickException(f"Job {job_id} not form-mapped. Run: python cli.py map-form {job_id}")

        print_job_header(job)
        print_resume_section(llm_cache['tailored_resume'])
        print_cover_letter(llm_cache['cover_letter'])
        print_qa_responses(llm_cache['qa_responses'])

        if form_cache:
            print_form_mapping(form_cache['field_mapping'], form_cache['form_fields'])

        if prompt_review_approval():
            click.echo("\nProceeding with submission...")
            click.echo(f"Run: python cli.py submit {job_id}")
        else:
            click.echo("\nApplication review cancelled.")

    except Exception as e:
        logger.error(f"Review failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
def summary():
    """Show overall application summary"""
    try:
        config = get_config()
        db = JobberDB(config.db_path)
        stats = db.get_stats()
        print_summary(stats)
    except Exception as e:
        logger.error(f"Summary failed: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()
