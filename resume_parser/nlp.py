# resume_parser/nlp.py

import re
from typing import List, Dict
from .schema import empty_resume_schema

# Expandable skills database
SKILLS_DB = {
    "python", "java", "c", "c++", "c#", "javascript", "typescript",
    "html", "css", "react", "node.js", "express", "django", "flask",
    "sql", "mysql", "postgresql", "mongodb", "nosql", "oracle",
    "git", "github", "docker",
    "flutter", "dart",
    "machine learning", "deep learning", "nlp",
    "data analysis", "excel",
    "uipath", "rpa"
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_email(text: str) -> str:
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = re.search(r"\+?\d[\d\s\-]{8,}\d", text)
    return m.group(0).strip() if m else ""


def extract_name(text: str) -> str:
    """
    Very heuristic: look at first 5 lines and choose a 'nice' non-email/phone line.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        if "@" in line:
            continue
        if re.search(r"\d", line):
            continue
        words = line.split()
        if 1 < len(words) <= 4:
            return line
    return ""


def find_section_block(text: str, keywords: List[str]) -> str:
    """
    Find a section in the resume like 'Education', 'Experience', etc.
    Returns raw block of text until next ALL CAPS / keyword-like heading.
    """
    lines = text.splitlines()
    lowered = [l.lower() for l in lines]

    start_idx = None
    for i, line in enumerate(lowered):
        for kw in keywords:
            if re.fullmatch(rf"{re.escape(kw)}[:]?", line.strip(), flags=re.IGNORECASE):
                start_idx = i
                break
        if start_idx is not None:
            break

    if start_idx is None:
        return ""

    # content until next probable heading
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        l = lines[j].strip()
        if (l.isupper() and len(l.split()) <= 5) or re.match(r"^[A-Za-z ]+[:]\s*$", l):
            end_idx = j
            break

    return "\n".join(lines[start_idx + 1:end_idx]).strip()


def section_to_list(section_text: str) -> List[str]:
    """Convert bullet/line separated section into a list of entries."""
    res = []
    for line in section_text.splitlines():
        line = line.strip(" -•\t")
        if line:
            res.append(line)
    return res


def extract_skills(text: str) -> List[str]:
    found = []
    t = text.lower()
    for skill in SKILLS_DB:
        if skill.lower() in t:
            found.append(skill)
    return sorted(set(found), key=str.lower)


def parse_education(text: str, schema: Dict) -> None:
    """
    Very heuristic education parser.
    Fills: high school, UG, PG fields where possible.
    """
    edu_block = find_section_block(text, ["education", "academics", "academic details"])
    if not edu_block:
        return

    lines = [l.strip() for l in edu_block.splitlines() if l.strip()]

    for line in lines:
        l = line.lower()

        # High School (10th / 12th merged)
        if any(k in l for k in ["10th", "x ", "ssc", "matric", "high school"]):
            schema["highSchoolName"] = schema["highSchoolName"] or line
            # Try to find percentage / GPA
            perc = re.search(r"\b\d{2,3}\.?(\d+)?\s*%", line)
            cgpa = re.search(r"\b\d\.\d{1,2}\b", line)
            year = re.search(r"\b(19|20)\d{2}\b", line)

            if perc:
                schema["highSchoolGpaOrPercentage"] = perc.group(0)
                schema["highSchoolGpaScale"] = "percentage"
            elif cgpa:
                schema["highSchoolGpaOrPercentage"] = cgpa.group(0)
                schema["highSchoolGpaScale"] = "cgpa"

            if year:
                schema["highSchoolGraduationYear"] = year.group(0)

        # UG
        elif any(k in l for k in ["b.tech", "b.e", "bsc", "bca", "b.com", "bachelor"]):
            schema["ugCollegeName"] = schema["ugCollegeName"] or line
            schema["ugDegree"] = schema["ugDegree"] or "Bachelor"
            # Major in parentheses
            major = re.search(r"\(([^)]+)\)", line)
            if major:
                schema["ugMajor"] = major.group(1)
            # marks
            perc = re.search(r"\b\d{2,3}\.?(\d+)?\s*%", line)
            cgpa = re.search(r"\b\d\.\d{1,2}\b", line)
            year = re.search(r"\b(19|20)\d{2}\b", line)
            if perc:
                schema["ugCollegeGpaOrPercentage"] = perc.group(0)
                schema["ugCollegeGpaScale"] = "percentage"
            elif cgpa:
                schema["ugCollegeGpaOrPercentage"] = cgpa.group(0)
                schema["ugCollegeGpaScale"] = "cgpa"
            if year:
                schema["ugGraduationYear"] = year.group(0)

        # PG
        elif any(k in l for k in ["m.tech", "m.e", "msc", "mca", "mba", "master"]):
            schema["pgCollegeName"] = schema["pgCollegeName"] or line
            schema["pgDegree"] = schema["pgDegree"] or "Master"
            major = re.search(r"\(([^)]+)\)", line)
            if major:
                schema["pgMajor"] = major.group(1)
            perc = re.search(r"\b\d{2,3}\.?(\d+)?\s*%", line)
            cgpa = re.search(r"\b\d\.\d{1,2}\b", line)
            year = re.search(r"\b(19|20)\d{2}\b", line)
            if perc:
                schema["pgCollegeGpaOrPercentage"] = perc.group(0)
                schema["pgCollegeGpaScale"] = "percentage"
            elif cgpa:
                schema["pgCollegeGpaOrPercentage"] = cgpa.group(0)
                schema["pgCollegeGpaScale"] = "cgpa"
            if year:
                schema["pgGraduationYear"] = year.group(0)


def parse_test_scores(text: str, schema: Dict) -> None:
    lower = text.lower()

    def grab_score(keyword: str) -> str:
        # e.g. "GRE: 320" or "GRE - 320"
        patt = rf"{keyword}\s*[:\-]\s*(\d+)"
        m = re.search(patt, lower)
        return m.group(1) if m else ""

    schema["testScores"]["gre"] = grab_score("gre") or schema["testScores"]["gre"]
    schema["testScores"]["gmat"] = grab_score("gmat") or schema["testScores"]["gmat"]
    schema["testScores"]["sat"] = grab_score("sat") or schema["testScores"]["sat"]
    schema["testScores"]["act"] = grab_score("act") or schema["testScores"]["act"]
    schema["testScores"]["toefl"] = grab_score("toefl") or schema["testScores"]["toefl"]
    schema["testScores"]["ielts"] = grab_score("ielts") or schema["testScores"]["ielts"]


def build_structured_data(text: str) -> Dict:
    """
    Main NLP pipeline:
    - extracts basic contact info
    - fills education / skills / sections into schema
    """
    schema = empty_resume_schema()

    # Basic info
    schema["name"] = extract_name(text)
    schema["email"] = extract_email(text)
    schema["phoneNumber"] = extract_phone(text)

    # Sections as list
    exp_block = find_section_block(text, ["experience", "work experience", "professional experience"])
    cert_block = find_section_block(text, ["certifications", "certification"])
    extra_block = find_section_block(text, ["extra curricular", "extracurricular", "activities"])
    ach_block = find_section_block(text, ["achievements", "accomplishments"])
    pubs_block = find_section_block(text, ["publications", "research", "research publications"])

    schema["workExperience"] = section_to_list(exp_block)
    schema["certifications"] = section_to_list(cert_block)
    schema["extraCurricularActivities"] = section_to_list(extra_block)
    schema["achievements"] = section_to_list(ach_block)
    schema["researchPublications"] = section_to_list(pubs_block)

    # Skills
    schema["skills"] = extract_skills(text)

    # Education + scores
    parse_education(text, schema)
    parse_test_scores(text, schema)

    return schema
