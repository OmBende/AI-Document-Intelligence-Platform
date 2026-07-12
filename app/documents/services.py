import json
import os
import uuid

from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.extraction.services import (
    extract_structured_data,
    extract_text
)
from app.models import Document, ExtractedField

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


def save_uploaded_document(uploaded_file, document_type):
    print(">>> save_uploaded_document() called")
    original_filename = secure_filename(uploaded_file.filename)
    extension = os.path.splitext(original_filename)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}{extension}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, stored_filename)
    uploaded_file.save(file_path)

    extracted_text = extract_text(file_path)
    print("\n========== EXTRACTED TEXT ==========")
    print(extracted_text[:1000])
    print("====================================\n")

    document = Document(
        filename=stored_filename,
        original_filename=original_filename,
        document_type=document_type,
        status="Processing" if extracted_text else "Extraction Failed",
        extracted_text=extracted_text,
        user_id=current_user.id
    )

    db.session.add(document)
    db.session.commit()
    
    if extracted_text:
        print(">>> Calling extract_structured_data()")
        structured_data = extract_structured_data(
            extracted_text=extracted_text,
            document_type=document_type
        )

        flattened_data = flatten_structured_data(structured_data)

        for field_name, field_value in flattened_data.items():
            extracted_field = ExtractedField(
                field_name=field_name,
                field_value=field_value,
                confidence=0.85,
                document_id=document.id
            )

            db.session.add(extracted_field)

        document.status = "Completed"
        db.session.commit()

    return document