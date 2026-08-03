"""Pretty-print review UI for HITL workflow."""

import click
from typing import Dict, List, Any


def print_job_header(job: Dict):
    """Print job header."""
    click.echo(click.style("\n" + "="*60, fg="blue"))
    click.echo(click.style(f"  {job['title']}", fg="blue", bold=True))
    click.echo(click.style(f"  {job['company']}", fg="blue"))
    click.echo(click.style(f"  URL: {job['url']}", fg="cyan"))
    click.echo(click.style("="*60 + "\n", fg="blue"))


def print_resume_section(tailored_resume: Dict):
    """Print tailored resume."""
    click.echo(click.style("\n[TAILORED RESUME]", fg="green", bold=True))
    click.echo(click.style("-"*60, fg="green"))

    click.echo(f"\nName: {tailored_resume.get('name')}")
    click.echo(f"Email: {tailored_resume.get('email')}")
    click.echo(f"Phone: {tailored_resume.get('phone')}")

    click.echo(f"\nSummary: {tailored_resume.get('summary', 'N/A')}")

    skills = tailored_resume.get('skills', [])
    if skills:
        click.echo(f"\nSkills ({len(skills)}):")
        for skill in skills[:10]:
            click.echo(f"  • {skill}")
        if len(skills) > 10:
            click.echo(f"  ... and {len(skills) - 10} more")

    experience = tailored_resume.get('experience', [])
    if experience:
        click.echo(f"\nExperience ({len(experience)}):")
        for exp in experience[:2]:
            click.echo(f"  • {exp.get('title')} at {exp.get('company')} ({exp.get('duration')})")
        if len(experience) > 2:
            click.echo(f"  ... and {len(experience) - 2} more")

    education = tailored_resume.get('education', [])
    if education:
        click.echo(f"\nEducation ({len(education)}):")
        for edu in education:
            click.echo(f"  • {edu.get('degree')} from {edu.get('school')} ({edu.get('year')})")


def print_cover_letter(cover_letter: str):
    """Print cover letter."""
    click.echo(click.style("\n[COVER LETTER]", fg="yellow", bold=True))
    click.echo(click.style("-"*60, fg="yellow"))
    click.echo(f"\n{cover_letter}\n")


def print_qa_responses(qa_responses: List[Dict]):
    """Print Q&A responses."""
    click.echo(click.style("\n[Q&A RESPONSES]", fg="cyan", bold=True))
    click.echo(click.style("-"*60, fg="cyan"))

    for i, qa in enumerate(qa_responses, 1):
        click.echo(f"\n{i}. Q: {qa.get('question')}")
        click.echo(f"   A: {qa.get('answer')}\n")


def print_form_mapping(form_mapping: Dict, form_fields: List[Dict]):
    """Print form field mapping."""
    click.echo(click.style("\n[FORM MAPPING]", fg="magenta", bold=True))
    click.echo(click.style("-"*60, fg="magenta"))

    total = len(form_fields)
    mapped = len(form_mapping)
    click.echo(f"\nMapped: {mapped}/{total} fields ({mapped*100//total}%)\n")

    for field in form_fields[:10]:
        name = field.get('name')
        value = form_mapping.get(name, '[UNMAPPED]')
        preview = value[:40] + "..." if len(str(value)) > 40 else value
        status = click.style("[OK]", fg="green") if value else click.style("[XX]", fg="red")
        click.echo(f"  {status} {name}: {preview}")

    if total > 10:
        click.echo(f"  ... and {total - 10} more fields")


def prompt_review_approval() -> bool:
    """Prompt user to approve or reject application."""
    click.echo("\n" + click.style("-"*60, fg="blue"))
    response = click.prompt(
        click.style("Approve and submit this application?", fg="blue", bold=True),
        type=click.Choice(["yes", "no"]),
        default="no"
    )
    return response.lower() == "yes"


def print_submission_result(success: bool, job_id: int):
    """Print submission result."""
    if success:
        click.echo(click.style(f"\n[OK] Application {job_id} SUBMITTED SUCCESSFULLY!", fg="green", bold=True))
    else:
        click.echo(click.style(f"\n[FAIL] Application {job_id} SUBMISSION FAILED", fg="red", bold=True))


def print_summary(stats: Dict):
    """Print application summary."""
    click.echo(click.style("\n" + "="*60, fg="blue"))
    click.echo(click.style("  APPLICATION SUMMARY", fg="blue", bold=True))
    click.echo(click.style("="*60, fg="blue"))

    click.echo(f"\nTotal Jobs Discovered: {stats['total_jobs_discovered']}")
    click.echo(f"Total Applications: {stats['total_applications']}")
    click.echo(f"  • Submitted: {stats['submitted_applications']}")
    click.echo(f"  • Pending: {stats['pending_applications']}")

    if stats['submitted_applications'] > 0:
        rate = (stats['submitted_applications'] / stats['total_applications']) * 100
        click.echo(f"\nSubmission Rate: {rate:.1f}%")
