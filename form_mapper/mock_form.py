"""Mock form HTML for testing form parsing and mapping."""

MOCK_FORM_HTML = """
<html>
<head><title>Job Application</title></head>
<body>
    <h1>Job Application Form</h1>
    <form id="application-form">
        <div>
            <label for="full_name">Full Name *</label>
            <input type="text" id="full_name" name="full_name" required />
        </div>

        <div>
            <label for="email">Email Address *</label>
            <input type="email" id="email" name="email" required />
        </div>

        <div>
            <label for="phone">Phone Number</label>
            <input type="tel" id="phone" name="phone" />
        </div>

        <div>
            <label for="skills">Technical Skills *</label>
            <textarea id="skills" name="skills" required></textarea>
        </div>

        <div>
            <label for="experience">Years of Experience</label>
            <select id="experience" name="experience">
                <option>Select</option>
                <option>0-1 years</option>
                <option>1-3 years</option>
                <option>3-5 years</option>
                <option>5+ years</option>
            </select>
        </div>

        <div>
            <label for="education">Education</label>
            <textarea id="education" name="education"></textarea>
        </div>

        <div>
            <label for="cover_letter">Cover Letter</label>
            <textarea id="cover_letter" name="cover_letter"></textarea>
        </div>

        <div>
            <label for="resume">Resume (PDF)</label>
            <input type="file" id="resume" name="resume" accept=".pdf" />
        </div>

        <div>
            <input type="checkbox" id="agree" name="agree" required />
            <label for="agree">I agree to the terms</label>
        </div>

        <button type="submit">Submit Application</button>
    </form>
</body>
</html>
"""
