import os
import uuid

from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Document


def save_uploaded_document(uploaded_file, document_type):
    """
    Save uploaded file to disk and metadata to the database.
    """

    original_filename = secure_filename(uploaded_file.filename)

    extension = os.path.splitext(original_filename)[1]

    stored_filename = f"{uuid.uuid4().hex}{extension}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, stored_filename)

    uploaded_file.save(file_path)

    document = Document(
        filename=stored_filename,
        original_filename=original_filename,
        document_type=document_type,
        status="Uploaded",
        user_id=current_user.id
    )

    db.session.add(document)
    db.session.commit()

    return document