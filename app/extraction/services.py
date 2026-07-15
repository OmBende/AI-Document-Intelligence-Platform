import os
import json

import requests
import pdfplumber
import pytesseract
from docx import Document as DocxDocument
from flask import current_app
from PIL import Image
from pdf2image import convert_from_path

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

def extract_text_from_scanned_pdf(file_path):
    """
    Convert scanned PDF pages to images and extract text using OCR.
    """
    configure_tesseract()

    poppler_path = current_app.config.get("POPPLER_PATH")

    pages = convert_from_path(
        file_path,
        dpi=300,
        poppler_path=poppler_path
    )

    extracted_pages = []

    for page_number, page_image in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(
            page_image,
            lang="eng",
            config="--psm 6"
        ).strip()

        if page_text:
            extracted_pages.append(
                f"--- Page {page_number} ---\n{page_text}"
            )

    return "\n\n".join(extracted_pages).strip()

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

    with Image.open(file_path) as image:
        image = image.convert("L")

        text = pytesseract.image_to_string(
            image,
            lang="eng",
            config="--psm 6"
        )

    return text.strip()

def extract_text(file_path):
    """
    Choose the correct extraction method based on file type.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        text = extract_text_from_pdf(file_path)

        if text:
            return text

        return extract_text_from_scanned_pdf(file_path)

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

def extract_invoice_data(text):
    print(">>> extract_invoice_data()")

    prompt = f"""
You are an accurate invoice information extraction system.

Return ONLY valid JSON with exactly these keys:

{{
  "invoice_number": null,
  "invoice_date": null,
  "due_date": null,
  "vendor_name": null,
  "customer_name": null,
  "subtotal": null,
  "tax": null,
  "total_amount": null,
  "currency": null
}}

Rules:
1. Extract actual values only.
2. Do not use headings as values.
3. Do not invent missing information.
4. Preserve amounts exactly as shown.
5. Return null when a field is unavailable.
6. Return JSON only.

Invoice text:

{text}
"""

    return ask_ollama(prompt)

def extract_receipt_data(text):
    print(">>> extract_receipt_data()")

    prompt = f"""
You are an accurate receipt information extraction system.

Return ONLY valid JSON with exactly these keys:

{{
  "merchant_name": null,
  "receipt_number": null,
  "date": null,
  "time": null,
  "subtotal": null,
  "tax": null,
  "total_amount": null,
  "payment_method": null,
  "currency": null,
  "items": []
}}

Each item should follow this structure:

{{
  "name": null,
  "quantity": null,
  "price": null
}}

Rules:
1. Extract actual values only.
2. Do not invent items or prices.
3. Keep items inside a JSON array.
4. Preserve amounts exactly as shown.
5. Return null when unavailable.
6. Return JSON only.

Receipt text:

{text}
"""

    return ask_ollama(prompt)

def extract_certificate_data(text):
    print(">>> extract_certificate_data()")

    prompt = f"""
You are an accurate certificate information extraction system.

Return ONLY valid JSON with exactly these keys:

{{
  "certificate_type": null,
  "recipient_name": null,
  "certificate_title": null,
  "issuing_organization": null,
  "course_or_program": null,
  "role_or_achievement": null,
  "issue_date": null,
  "start_date": null,
  "end_date": null,
  "duration": null,
  "grade_or_score": null,
  "credential_id": null,
  "certificate_number": null,
  "verification_url": null,
  "signatories": [],
  "location": null,
  "description": null
}}

Allowed certificate types include:
- Academic
- Internship
- Training
- Course Completion
- Employment
- Achievement
- Participation
- Appreciation
- Certification
- Other

Rules:
1. Extract only information explicitly present in the certificate.
2. Identify the most suitable certificate_type.
3. Extract the recipient's actual full name.
4. Extract the exact certificate title or heading.
5. Extract the issuing institution, company, university, or organization.
6. For internship or employment certificates, extract role, department, dates, and duration where available.
7. For course certificates, extract the course or program name.
8. For academic certificates, extract grade, score, rank, or result if present.
9. Extract credential ID, certificate number, and verification URL only when explicitly shown.
10. Extract names of signatories into the signatories array.
11. Do not use headings such as "Certificate", "Issued To", or "Completion" as values.
12. Do not invent missing dates, IDs, URLs, grades, or names.
13. Use null for unavailable single values.
14. Use an empty array for unavailable signatories.
15. Return JSON only, with no markdown or explanation.

Certificate text:

{text}
"""

    return ask_ollama(prompt)
def extract_contract_data(text):
    print(">>> extract_contract_data()")

    prompt = f"""
You are an accurate contract information extraction system.

Return ONLY valid JSON with exactly these keys:

{{
  "contract_title": null,
  "contract_number": null,
  "effective_date": null,
  "expiry_date": null,
  "parties": [],
  "contract_value": null,
  "currency": null,
  "payment_terms": null,
  "termination_clause": null,
  "governing_law": null,
  "obligations": [],
  "important_clauses": []
}}

Rules:
1. Extract only information explicitly present in the contract.
2. Do not invent parties, dates, amounts, clauses, or obligations.
3. Keep multiple parties, obligations, and clauses inside JSON arrays.
4. Preserve dates and amounts as written.
5. Return null when a value is unavailable.
6. Do not return section headings as values.
7. Return JSON only, without markdown or explanations.

Contract text:

{text}
"""

    return ask_ollama(prompt)   

def generate_document_summary(text, document_type):

    document_type = document_type.lower()

    if document_type == "resume":
        return generate_resume_summary(text)

    elif document_type == "invoice":
        return generate_invoice_summary(text)

    elif document_type == "receipt":
        return generate_receipt_summary(text)

    elif document_type == "contract":
        return generate_contract_summary(text)

    elif document_type == "certificate":
        return generate_certificate_summary(text)

    elif document_type == "form":
        return generate_form_summary(text)

    else:
        return generate_generic_summary(text)
    
def extract_summary_from_response(prompt):
    """
    Safely retrieve a summary from Ollama's JSON response.
    """
    result = ask_ollama(prompt)

    print("SUMMARY RESPONSE:", result)

    if not isinstance(result, dict):
        return "No summary could be generated."

    summary = result.get("summary")

    if not summary:
        return "No summary could be generated."

    return str(summary).strip()

def generate_resume_summary(text):
    prompt = f"""
You are an expert resume summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a professional summary in 2 to 3 sentences.

Mention:
- Candidate name
- Experience
- Technical skills
- Education
- Major strengths

Use only information present in the resume.
Do not include markdown or explanations.

Resume text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_invoice_summary(text):
    prompt = f"""
You are an accurate invoice summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 1 to 3 sentences.

Mention when available:
- Vendor
- Customer
- Invoice number
- Invoice date
- Due date
- Total amount
- Currency

Do not invent missing information.
Do not include markdown or explanations.

Invoice text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_receipt_summary(text):
    prompt = f"""
You are an accurate receipt summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 1 to 3 sentences.

Mention when available:
- Merchant
- Receipt date
- Purchased items
- Total amount
- Currency
- Payment method

Do not invent missing information.
Do not include markdown or explanations.

Receipt text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_contract_summary(text):
    prompt = f"""
You are an accurate contract summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 2 to 4 sentences.

Mention when available:
- Contract title
- Parties
- Purpose
- Effective date
- Expiry date
- Contract value
- Important obligations or clauses

Do not provide legal advice.
Do not invent missing information.
Do not include markdown or explanations.

Contract text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_certificate_summary(text):
    prompt = f"""
You are an accurate certificate summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 1 to 3 sentences.

Mention when available:
- Recipient
- Certificate title or type
- Issuing organization
- Course, role, or achievement
- Issue date
- Duration

Do not invent missing information.
Do not include markdown or explanations.

Certificate text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_form_summary(text):
    prompt = f"""
You are an accurate form summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 1 to 3 sentences.

Mention when available:
- Form title or type
- Applicant
- Purpose
- Application or reference number
- Important submitted details

Do not invent missing information.
Do not include markdown or explanations.

Form text:

{text}
"""

    return extract_summary_from_response(prompt)


def generate_generic_summary(text):
    prompt = f"""
You are an accurate document summarizer.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": ""
}}

Write a concise summary in 2 to 3 sentences using only the information
explicitly present in the document.

Do not invent information.
Do not include markdown or explanations.

Document text:

{text}
"""

    return extract_summary_from_response(prompt)

def extract_structured_data(extracted_text, document_type):
    print(">>> extract_structured_data()")

    normalized_type = document_type.strip().lower()

    if normalized_type == "resume":
        structured_data = extract_basic_info(extracted_text)
        structured_data["tech_skills"] = extract_skills(extracted_text)
        return structured_data

    if normalized_type == "invoice":
        return extract_invoice_data(extracted_text)

    if normalized_type == "receipt":
        return extract_receipt_data(extracted_text)

    if normalized_type == "contract":
        return extract_contract_data(extracted_text)

    if normalized_type == "certificate":
        return extract_certificate_data(extracted_text)

    return {
        "document_text_preview": extracted_text[:1000]
    }