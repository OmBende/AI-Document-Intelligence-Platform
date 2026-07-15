import json
import os
import re
import uuid
from app.constants import (
    DOCUMENT_STATUS_PROCESSING,
    DOCUMENT_STATUS_COMPLETED,
    DOCUMENT_STATUS_NEEDS_REVIEW,
    DOCUMENT_STATUS_EXTRACTION_FAILED,
    REVIEW_STATUS_PENDING
)
from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.extraction.services import (
    extract_structured_data,
    extract_text,
    generate_document_summary
)
from app.models import Document, ExtractedField, ReviewQueue


def flatten_structured_data(data, parent_key=""):
    """
    Convert nested AI JSON into flat field-name/value pairs.
    """
    flattened = {}

    for key, value in data.items():
        field_name = f"{parent_key}_{key}" if parent_key else key

        if isinstance(value, dict):
            flattened.update(
                flatten_structured_data(
                    value,
                    parent_key=field_name
                )
            )

        elif isinstance(value, list):
            if all(
                not isinstance(item, (dict, list))
                for item in value
            ):
                flattened[field_name] = ", ".join(
                    str(item) for item in value
                )
            else:
                for index, item in enumerate(value, start=1):
                    indexed_name = f"{field_name}_{index}"

                    if isinstance(item, dict):
                        flattened.update(
                            flatten_structured_data(
                                item,
                                parent_key=indexed_name
                            )
                        )
                    else:
                        flattened[indexed_name] = json.dumps(
                            item,
                            ensure_ascii=False
                        )

        elif value is None:
            flattened[field_name] = ""

        else:
            flattened[field_name] = str(value)

    return flattened


def calculate_confidence(field_name, field_value):
    """
    Calculate a basic validation-based confidence score.
    """
    value = str(field_value).strip()

    if not value:
        return 0.30

    normalized_name = field_name.lower()

    if "email" in normalized_name:
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return 0.98 if re.match(email_pattern, value) else 0.45

    if "phone" in normalized_name:
        digits = re.sub(r"\D", "", value)
        return 0.95 if 10 <= len(digits) <= 15 else 0.50

    if normalized_name in {"linkedin", "github"}:
        if value.lower() in {
            "",
            "none",
            "null",
            "linkedin",
            "github"
        }:
            return 0.35

        return 0.90

    if len(value) < 2:
        return 0.45

    return 0.85


def save_uploaded_document(uploaded_file, document_type):
    """
    Save, process and store an uploaded document.
    """
    original_filename = secure_filename(uploaded_file.filename)
    extension = os.path.splitext(original_filename)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}{extension}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, stored_filename)
    uploaded_file.save(file_path)

    extracted_text = extract_text(file_path)

    document = Document(
        filename=stored_filename,
        original_filename=original_filename,
        document_type=document_type,
        status=(
                DOCUMENT_STATUS_PROCESSING
                if extracted_text
                else DOCUMENT_STATUS_EXTRACTION_FAILED  
            ),
        extracted_text=extracted_text,
        user_id=current_user.id
    )

    db.session.add(document)
    db.session.commit()

    if not extracted_text:
        return document

    structured_data = extract_structured_data(
        extracted_text=extracted_text,
        document_type=document_type
    )
    ai_summary = generate_document_summary(
    text=extracted_text,
    document_type=document_type
)

    document.ai_summary = ai_summary

    flattened_data = flatten_structured_data(structured_data)
    has_pending_reviews = False

    for field_name, field_value in flattened_data.items():
        confidence = calculate_confidence(
            field_name,
            field_value
        )

        extracted_field = ExtractedField(
            field_name=field_name,
            field_value=field_value,
            confidence=confidence,
            document_id=document.id
        )

        db.session.add(extracted_field)

        if confidence < 0.80:
            has_pending_reviews = True

            review_item = ReviewQueue(
                document_id=document.id,
                field_name=field_name,
                old_value=field_value,
                status=REVIEW_STATUS_PENDING
            )

            db.session.add(review_item)

    document.status = (
    DOCUMENT_STATUS_NEEDS_REVIEW
    if has_pending_reviews
    else DOCUMENT_STATUS_COMPLETED
)

    db.session.commit()

    return document