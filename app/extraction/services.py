import os
import json

import requests
import pdfplumber
import pytesseract
from docx import Document as DocxDocument
from flask import current_app
from PIL import Image


def configure_tesseract():
    """
    Configure the Tesseract executable.
    """
    tesseract_cmd = current_app.config.get("TESSERACT_CMD")

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def extract_text_from_pdf(file_path):
    extracted_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text.append(page_text)

    return "\n".join(extracted_text).strip()


def extract_text_from_docx(file_path):
    document = DocxDocument(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs).strip()


def extract_text_from_image(file_path):
    """
    OCR for images.
    """
    configure_tesseract()

    image = Image.open(file_path)

    text = pytesseract.image_to_string(
        image,
        lang="eng"
    )

    return text.strip()


def extract_text(file_path):

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    if extension in [".jpg", ".jpeg", ".png"]:
        return extract_text_from_image(file_path)

    return ""

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()
    raw_output = result.get("response", "{}")

    print("\n==============================")
    print(raw_output)
    print("==============================\n")

    return json.loads(raw_output)

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()
    raw_output = result.get("response", "{}")

    print("\n==============================")
    print(raw_output)
    print("==============================\n")

    return json.loads(raw_output)


def extract_basic_info(text):
    print(">>> extract_basic_info()")

    prompt = f"""
You are an expert resume parser.

The candidate's full name is usually the FIRST prominent line at the top of the resume.

Return ONLY valid JSON with exactly these keys:

{{
    "name": null,
    "email": null,
    "phone": null,
    "linkedin": null,
    "github": null
}}

Rules:
1. Extract the candidate's full name from the top of the resume.
2. Extract the actual email address.
3. Extract the actual phone number.
4. Extract the actual LinkedIn URL or username. If unavailable, return null.
5. Extract the actual GitHub URL or username. If unavailable, return null.
6. Never return headings such as "Contact Information", "LinkedIn", or "GitHub".
7. Never return true or false.
8. Never invent information.
9. Return JSON only.

Resume:

{text}
"""

    return ask_ollama(prompt)


def extract_skills(text):
    print(">>> extract_skills()")
    prompt = f"""
Return ONLY valid JSON with exactly these keys:

{{
  "languages": [],
  "frameworks": [],
  "databases": [],
  "tools": []
}}

Rules:
1. Extract only technical skills.
2. Keep every value inside an array.
3. Do not include explanations.
4. Do not invent skills.

Resume:

{text}
"""

    return ask_ollama(prompt)


def extract_structured_data(extracted_text, document_type):
    print(">>> extract_structured_data()")
    if document_type.lower() != "resume":
        return extract_basic_info(extracted_text)

    structured_data = extract_basic_info(extracted_text)

    structured_data["tech_skills"] = extract_skills(
        extracted_text
    )

    return structured_data