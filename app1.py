#!/usr/bin/env python3
"""
Resume Extractor & Parser with Web UI (Flask)

Features:
- Upload PDF / DOCX / TXT resumes via browser
- Extracts: name, email, phone, links, skills, summary, education, experience, projects
- Shows nicely in HTML
"""

import re
import os
import json
import tempfile
from typing import List, Dict, Optional

from flask import Flask, request, render_template_string

import pdfplumber       # for PDFs
import docx             # for DOCX

# =========================
# FLASK APP SETUP
# =========================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max upload


# =========================
# TEXT EXTRACTION
# =========================

def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    return "\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext in [".txt", ".text"]:
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")


# =========================
# BASIC PARSING HELPERS
# =========================

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d{1,3}[-.\s]?)?(\d{3,5}[-.\s]?\d{3,5}[-.\s]?\d{3,5})"
URL_REGEX   = r"(https?://[^\s]+|www\.[^\s]+)"

SKILLS_DB = {
    "python", "java", "c", "c++", "c#", "javascript", "typescript",
    "html", "css", "react", "node.js", "express", "django", "flask",
    "sql", "mysql", "postgresql", "mongodb", "nosql", "oracle",
    "git", "github", "docker", "kubernetes",
    "flutter", "dart",
    "aws", "azure", "gcp",
    "machine learning", "deep learning", "nlp", "data analysis",
    "ui/ux", "figma", "canva",
    "rpa", "uipath"
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_email(text: str) -> Optional[str]:
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    matches = re.findall(PHONE_REGEX, text)
    if not matches:
        return None

    for match in matches:
        candidate = "".join(match)
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 13:
            return candidate.strip()
    return None


def extract_links(text: str) -> List[str]:
    return re.findall(URL_REGEX, text)


def guess_name(lines: List[str]) -> Optional[str]:
    for line in lines[:8]:
        line_clean = line.strip()
        if not line_clean:
            continue
        if re.search(EMAIL_REGEX, line_clean):
            continue
        if re.search(URL_REGEX, line_clean):
            continue
        if re.search(PHONE_REGEX, line_clean):
            continue

        words = line_clean.split()
        if 1 < len(words) <= 4:
            if all(any(ch.isalpha() for ch in w) for w in words):
                return line_clean
    return None


def extract_skills(text: str, skills_db: set) -> List[str]:
    text_lower = text.lower()
    found = []
    for skill in skills_db:
        if skill.lower() in text_lower:
            found.append(skill)
    return sorted(set(found), key=str.lower)


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


# =========================
# SECTION PARSING
# =========================

SECTION_HEADERS = {
    "summary": ["summary", "about me", "profile"],
    "education": ["education", "academic", "qualification", "academics"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["project", "projects"],
    "skills": ["skills", "technical skills", "skills & tools"]
}


def find_sections(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    index_to_section = {}

    for i, raw_line in enumerate(lines):
        line = raw_line.strip().lower()
        for section, keywords in SECTION_HEADERS.items():
            for kw in keywords:
                if re.fullmatch(rf"{re.escape(kw)}:?", line, flags=re.IGNORECASE):
                    index_to_section[i] = section

    sections_text: Dict[str, str] = {name: "" for name in SECTION_HEADERS.keys()}

    sorted_indices = sorted(index_to_section.keys())
    if not sorted_indices:
        sections_text["summary"] = text
        return sections_text

    for idx, start_line in enumerate(sorted_indices):
        section_name = index_to_section[start_line]
        end_line = sorted_indices[idx + 1] if idx + 1 < len(sorted_indices) else len(lines)
        content_lines = lines[start_line + 1: end_line]
        content = "\n".join(content_lines).strip()
        if sections_text[section_name]:
            sections_text[section_name] += "\n" + content
        else:
            sections_text[section_name] = content

    return sections_text


# =========================
# MAIN PARSER CLASS
# =========================

class ResumeParser:
    def __init__(self, skills_db: Optional[set] = None):
        self.skills_db = skills_db if skills_db is not None else SKILLS_DB

    def parse(self, file_path: str) -> Dict:
        raw_text = extract_text(file_path)
        raw_text_clean = clean_text(raw_text)
        lines = split_lines(raw_text)

        email = extract_email(raw_text)
        phone = extract_phone(raw_text)
        links = extract_links(raw_text)
        name = guess_name(lines)
        skills = extract_skills(raw_text, self.skills_db)

        sections = find_sections(raw_text)

        parsed = {
            "file_name": os.path.basename(file_path),
            "name": name,
            "email": email,
            "phone": phone,
            "links": links,
            "skills": skills,
            "summary": sections.get("summary") or None,
            "education": sections.get("education") or None,
            "experience": sections.get("experience") or None,
            "projects": sections.get("projects") or None,
            "raw_text": raw_text_clean
        }
        return parsed

    def parse_to_json(self, file_path: str) -> str:
        data = self.parse(file_path)
        return json.dumps(data, indent=2, ensure_ascii=False)


resume_parser = ResumeParser()


# =========================
# HTML TEMPLATE (INLINE)
# =========================

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Resume Parser</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <!-- Simple Bootstrap for UI -->
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    rel="stylesheet"
  >

  <style>
    body { background-color: #f5f5f7; }
    .card { border-radius: 16px; }
    pre {
      background: #111827;
      color: #e5e7eb;
      padding: 12px;
      border-radius: 10px;
      font-size: 0.85rem;
      max-height: 350px;
      overflow: auto;
    }
    .badge-skill {
      margin: 3px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #e0f2fe;
      color: #0369a1;
      font-size: 0.75rem;
    }
  </style>
</head>
<body>
<div class="container py-4">
  <h1 class="mb-3 text-center">📄 Resume Extractor & Parser</h1>
  <p class="text-center text-muted mb-4">
    Upload a PDF / DOCX / TXT resume and get structured information.
  </p>

  <div class="row justify-content-center">
    <div class="col-lg-8">
      <div class="card shadow-sm mb-4">
        <div class="card-body">
          <form method="POST" enctype="multipart/form-data">
            <div class="mb-3">
              <label for="file" class="form-label">Choose Resume File</label>
              <input class="form-control" type="file" name="file" id="file" required>
              <div class="form-text">
                Allowed: .pdf, .docx, .txt (max 10 MB)
              </div>
            </div>
            <button class="btn btn-primary" type="submit">Upload & Parse</button>
          </form>
        </div>
      </div>

      {% if error %}
      <div class="alert alert-danger">{{ error }}</div>
      {% endif %}

      {% if result %}
      <div class="card shadow-sm mb-4">
        <div class="card-body">
          <h5 class="card-title mb-3">Parsed Details</h5>

          <dl class="row mb-0">
            <dt class="col-sm-3">File</dt>
            <dd class="col-sm-9">{{ result.file_name }}</dd>

            <dt class="col-sm-3">Name</dt>
            <dd class="col-sm-9">{{ result.name or "-" }}</dd>

            <dt class="col-sm-3">Email</dt>
            <dd class="col-sm-9">{{ result.email or "-" }}</dd>

            <dt class="col-sm-3">Phone</dt>
            <dd class="col-sm-9">{{ result.phone or "-" }}</dd>

            <dt class="col-sm-3">Links</dt>
            <dd class="col-sm-9">
              {% if result.links %}
                {% for link in result.links %}
                  <div><a href="{{ link }}" target="_blank">{{ link }}</a></div>
                {% endfor %}
              {% else %}
                -
              {% endif %}
            </dd>

            <dt class="col-sm-3">Skills</dt>
            <dd class="col-sm-9">
              {% if result.skills %}
                {% for skill in result.skills %}
                  <span class="badge-skill">{{ skill }}</span>
                {% endfor %}
              {% else %}
                -
              {% endif %}
            </dd>
          </dl>
        </div>
      </div>

      <div class="accordion mb-4" id="accordionSections">
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingSummary">
            <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseSummary" aria-expanded="true">
              Summary / Profile
            </button>
          </h2>
          <div id="collapseSummary" class="accordion-collapse collapse show" data-bs-parent="#accordionSections">
            <div class="accordion-body">
              <pre>{{ result.summary or "No summary section detected." }}</pre>
            </div>
          </div>
        </div>

        <div class="accordion-item">
          <h2 class="accordion-header" id="headingEducation">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseEducation">
              Education
            </button>
          </h2>
          <div id="collapseEducation" class="accordion-collapse collapse" data-bs-parent="#accordionSections">
            <div class="accordion-body">
              <pre>{{ result.education or "No education section detected." }}</pre>
            </div>
          </div>
        </div>

        <div class="accordion-item">
          <h2 class="accordion-header" id="headingExperience">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseExperience">
              Experience
            </button>
          </h2>
          <div id="collapseExperience" class="accordion-collapse collapse" data-bs-parent="#accordionSections">
            <div class="accordion-body">
              <pre>{{ result.experience or "No experience section detected." }}</pre>
            </div>
          </div>
        </div>

        <div class="accordion-item">
          <h2 class="accordion-header" id="headingProjects">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseProjects">
              Projects
            </button>
          </h2>
          <div id="collapseProjects" class="accordion-collapse collapse" data-bs-parent="#accordionSections">
            <div class="accordion-body">
              <pre>{{ result.projects or "No projects section detected." }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title">Raw JSON</h5>
          <pre>{{ result_json }}</pre>
        </div>
      </div>
      {% endif %}
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


# =========================
# ROUTES
# =========================

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    result_json = None
    error = None

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            error = "Please choose a file."
        else:
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".pdf", ".docx", ".txt", ".text"]:
                error = "Unsupported file type. Use PDF, DOCX, or TXT."
            else:
                try:
                    # Save to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        file.save(tmp.name)
                        temp_path = tmp.name

                    parsed = resume_parser.parse(temp_path)
                    result = parsed
                    result_json = json.dumps(parsed, indent=2, ensure_ascii=False)

                except Exception as e:
                    error = f"Error while parsing file: {e}"
                finally:
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    return render_template_string(
        TEMPLATE,
        result=result,
        result_json=result_json,
        error=error,
    )


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    # debug=True only for development
    app.run(host="0.0.0.0", port=5000, debug=True)
