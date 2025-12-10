# resume_parser/schema.py

from copy import deepcopy

BASE_RESUME_SCHEMA = {
    "name": "",
    "email": "",
    "phoneNumber": "",

    "highSchoolName": "",
    "highSchoolAddress": "",
    "highSchoolGpaOrPercentage": "",
    "highSchoolGpaScale": "",
    "highSchoolBoard": "",
    "highSchoolGraduationYear": "",

    "ugCollegeName": "",
    "ugCollegeAddress": "",
    "ugCollegeGpaOrPercentage": "",
    "ugCollegeGpaScale": "",
    "ugUniversity": "",
    "ugGraduationYear": "",
    "ugDegree": "",
    "ugMajor": "",

    "pgCollegeName": "",
    "pgCollegeAddress": "",
    "pgCollegeGpaOrPercentage": "",
    "pgCollegeGpaScale": "",
    "pgUniversity": "",
    "pgGraduationYear": "",
    "pgDegree": "",
    "pgMajor": "",

    "certifications": [],              # list of strings
    "extraCurricularActivities": [],   # list of strings
    "workExperience": [],              # list of strings/paragraphs
    "researchPublications": [],        # list of strings

    "testScores": {
        "sat": "",
        "act": "",
        "gre": "",
        "gmat": "",
        "toefl": "",
        "ielts": ""
    },

    "achievements": [],                # list of strings
    "skills": []                       # list of strings
}


def empty_resume_schema() -> dict:
    """Return a *fresh* copy of the base schema so it doesn't get mutated."""
    return deepcopy(BASE_RESUME_SCHEMA)
