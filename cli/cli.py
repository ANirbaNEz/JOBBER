import click
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config, load_master_resume, validate_master_resume
from db.db import JobberDB
from logging_monitor.logger import setup_logger
from scraper.indeed_scraper import IndeedScraper
from scraper.mock_scraper import MockScraper


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


if __name__ == '__main__':
    cli()
