import os

import pdfplumber
from docx import Document as DocxDocument


def extract_text_from_pdf(file_path):
    """
    Extract text from a text-based PDF.
    """
    extracted_text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text.append(page_text)

    return "\n".join(extracted_text).strip()


def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.
    """
    document = DocxDocument(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs).strip()


def extract_text(file_path):
    """
    Select the correct extraction method based on file extension.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    return ""