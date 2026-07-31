# Jobber - Semi-Autonomous Job Application Agent

An intelligent job application agent that automates the process of finding jobs, tailoring resumes, and submitting applications with human-in-the-loop review.

## Features

- **Job Scraping**: Discover jobs from Indeed, LinkedIn, and ATS platforms
- **Resume Tailoring**: AI-powered resume customization using Gemini API
- **Cover Letter Generation**: Automated cover letter creation
- **Form Filling**: Intelligent form field mapping and filling
- **HITL Review**: Human-in-the-loop approval before every submission
- **Deduplication**: Prevents re-applying to the same job
- **Audit Trail**: Complete logging of all operations

## Architecture

### Modules

1. **Database Module** (`db/`) - SQLite-based job and application tracking
2. **Config Module** (`config/`) - Configuration management and master resume validation
3. **Scraper Module** (`scraper/`) - Job discovery from multiple sources
4. **LLM Engine** (`llm_engine/`) - Resume tailoring and cover letter generation using Gemini API
5. **Renderer Module** (`renderer/`) - PDF resume generation
6. **Form Mapper Module** (`form_mapper/`) - Application form parsing and field mapping
7. **Executor Module** (`executor/`) - Form submission and email-based applications
8. **CLI Module** (`cli/`) - User interface and workflow orchestration
9. **Logging Module** (`logging_monitor/`) - Structured logging and audit trail

## Setup

### Prerequisites

- Python 3.9+
- Gemini API key from Google
- SMTP credentials for email-based applications (optional)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd jobber
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp config/.env.template .env
   ```
   Edit `.env` and add your:
   - `GEMINI_API_KEY`
   - `SMTP_EMAIL` and `SMTP_PASSWORD` (optional)

3. **Update master resume**:
   Edit `config/master_resume.json` with your actual resume data.

4. **Initialize**:
   ```bash
   python cli/cli.py init
   ```

## Usage

### Initialize (Phase 1)
```bash
python cli/cli.py init
```
Loads master resume, validates schema, and sets up database.

### Scrape Jobs (Phase 2)
```bash
python cli/cli.py scrape --source indeed --limit 10
```
Discovers jobs and stores them in the database.

### Process & Review (Phase 3-8)
```bash
python cli/cli.py process <job_id>
```
Generates tailored resume and cover letter for human review.

### Submit Applications (Phase 6-7)
```bash
python cli/cli.py submit <job_id>
```
Fills forms and submits after user confirmation.

### View Status
```bash
python cli/cli.py status
python cli/cli.py jobs --limit 20
python cli/cli.py logs
```

## Workflow

```
1. Init (load master resume)
   ↓
2. Scrape (discover jobs)
   ↓
3. Process (LLM tailor resume + cover letter)
   ↓
4. Review (user reviews tailored content)
   ↓
5. Parse Forms (extract form fields)
   ↓
6. Map Fields (match resume data to form fields)
   ↓
7. Submit (fill forms, upload PDF, submit)
   ↓
8. Log (track in audit trail)
```

## Database Schema

- **discovered_jobs**: Job listings discovered during scraping
- **applications**: Application records with status tracking
- **form_mappings**: Cached form structures and field mappings
- **llm_cache**: Cached tailored resumes and cover letters
- **audit_log**: Complete audit trail of all operations

## Configuration

### .env Variables

```
GEMINI_API_KEY=<your-key>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=<your-email>
SMTP_PASSWORD=<your-password>
DB_PATH=./jobber.db
GENERATED_RESUMES_DIR=./generated_resumes
MASTER_RESUME_PATH=./config/master_resume.json
SCRAPER_DELAY=2
MAX_DAILY_APPLICATIONS=5
HEADLESS=true
BROWSER_TIMEOUT=30
```

## Implementation Phases

- **Phase 1**: ✅ Foundation (DB + Config)
- **Phase 2**: Scraper (Indeed, LinkedIn, ATS)
- **Phase 3**: LLM Engine (resume tailoring, cover letter generation)
- **Phase 4**: PDF Renderer
- **Phase 5**: Form Mapper
- **Phase 6**: Browser Executor
- **Phase 7**: Email Executor (SMTP)
- **Phase 8**: CLI Review & Approval
- **Phase 9**: Integration & Testing
- **Phase 10**: Polish & Documentation

## Safety & Compliance

- **No Hallucination**: Resume tailoring only subsets/reorders existing master resume skills
- **Deduplication**: Prevents duplicate applications via job URL hashing
- **HITL Review**: Every application requires human approval before submission
- **Rate Limiting**: Configurable delays between scrapes and submissions
- **Audit Trail**: Complete logging of all operations for accountability

## Contributing

This is an active development project. Each phase builds incrementally with comprehensive testing.

## License

MIT
