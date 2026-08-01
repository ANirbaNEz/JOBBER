from typing import Dict, Any


def generate_resume_html(tailored_resume: Dict[str, Any]) -> str:
    """Generate ATS-friendly HTML resume from tailored resume JSON."""

    name = tailored_resume.get("name", "")
    email = tailored_resume.get("email", "")
    phone = tailored_resume.get("phone", "")
    summary = tailored_resume.get("summary", "")
    skills = tailored_resume.get("skills", [])
    experience = tailored_resume.get("experience", [])
    education = tailored_resume.get("education", [])

    skills_html = ", ".join(skills)

    experience_html = ""
    for exp in experience:
        title = exp.get("title", "")
        company = exp.get("company", "")
        duration = exp.get("duration", "")
        description = exp.get("description", "")
        experience_html += f"""
        <div class="experience-item">
            <div class="job-header">
                <div class="job-title">{title}</div>
                <div class="duration">{duration}</div>
            </div>
            <div class="company">{company}</div>
            <div class="description">{description}</div>
        </div>
        """

    education_html = ""
    for edu in education:
        degree = edu.get("degree", "")
        school = edu.get("school", "")
        year = edu.get("year", "")
        education_html += f"""
        <div class="education-item">
            <div class="edu-header">
                <div class="degree">{degree}</div>
                <div class="year">{year}</div>
            </div>
            <div class="school">{school}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Resume</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.5;
            color: #333;
            background-color: white;
        }}

        .container {{
            max-width: 8.5in;
            height: 11in;
            margin: 0 auto;
            padding: 0.5in;
            background: white;
        }}

        header {{
            text-align: left;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 12px;
            margin-bottom: 16px;
        }}

        .name {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 4px;
        }}

        .contact {{
            font-size: 10px;
            color: #555;
        }}

        .contact span {{
            margin-right: 12px;
        }}

        section {{
            margin-bottom: 14px;
        }}

        .section-title {{
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
            text-transform: uppercase;
            border-bottom: 1px solid #bbb;
            padding-bottom: 4px;
            margin-bottom: 8px;
        }}

        .summary {{
            font-size: 10px;
            line-height: 1.4;
            margin-bottom: 8px;
            color: #444;
        }}

        .skills {{
            font-size: 10px;
            line-height: 1.4;
            color: #444;
        }}

        .experience-item {{
            margin-bottom: 10px;
            font-size: 10px;
        }}

        .job-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 2px;
        }}

        .job-title {{
            font-weight: bold;
            color: #2c3e50;
        }}

        .duration {{
            color: #666;
            font-style: italic;
        }}

        .company {{
            color: #555;
            font-weight: 500;
            margin-bottom: 2px;
        }}

        .description {{
            color: #444;
            line-height: 1.3;
            margin-bottom: 4px;
        }}

        .education-item {{
            margin-bottom: 8px;
            font-size: 10px;
        }}

        .edu-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 2px;
        }}

        .degree {{
            font-weight: bold;
            color: #2c3e50;
        }}

        .year {{
            color: #666;
        }}

        .school {{
            color: #555;
        }}

        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 100%;
                height: 100%;
                padding: 0.5in;
                margin: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="name">{name}</div>
            <div class="contact">
                <span>{email}</span>
                <span>{phone}</span>
            </div>
        </header>

        <section>
            <div class="section-title">Professional Summary</div>
            <div class="summary">{summary}</div>
        </section>

        <section>
            <div class="section-title">Skills</div>
            <div class="skills">{skills_html}</div>
        </section>

        <section>
            <div class="section-title">Experience</div>
            {experience_html}
        </section>

        <section>
            <div class="section-title">Education</div>
            {education_html}
        </section>
    </div>
</body>
</html>"""

    return html
