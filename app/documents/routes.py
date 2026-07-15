from flask import flash, abort, redirect, render_template, request, url_for
from flask_login import login_required,current_user
from sqlalchemy import or_
from app.extensions import db
from app.documents import documents_bp
from app.documents.forms import DocumentUploadForm
from app.documents.services import save_uploaded_document
from app.models import Document, ExtractedField

@documents_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = DocumentUploadForm()

    if form.validate_on_submit():

        save_uploaded_document(
            uploaded_file=form.document.data,
            document_type=form.document_type.data
        )

        flash(
            "Document uploaded successfully.",
            "success"
        )

        return redirect(url_for("dashboard.index"))

    return render_template(
        "documents/upload.html",
        form=form
    )

@documents_bp.route("/<int:document_id>")
@login_required
def detail(document_id):
    document = Document.query.filter_by(
        id=document_id,
        user_id=current_user.id
    ).first()

    if document is None:
        abort(404)

    fields = ExtractedField.query.filter_by(
        document_id=document.id
    ).order_by(
        ExtractedField.id.asc()
    ).all()

    average_confidence = 0

    if fields:
        average_confidence = round(
            sum(field.confidence for field in fields)
            / len(fields)
            * 100
        )

    return render_template(
        "documents/detail.html",
        document=document,
        fields=fields,
        average_confidence=average_confidence
    )


@documents_bp.route(
    "/<int:document_id>/fields/<int:field_id>/edit",
    methods=["POST"]
)
@login_required
def edit_field(document_id, field_id):
    document = Document.query.filter_by(
        id=document_id,
        user_id=current_user.id
    ).first()

    if document is None:
        abort(404)

    field = ExtractedField.query.filter_by(
        id=field_id,
        document_id=document.id
    ).first()

    if field is None:
        abort(404)

    new_value = request.form.get("field_value", "").strip()

    if not new_value:
        flash("Field value cannot be empty.", "danger")
        return redirect(
            url_for(
                "documents.detail",
                document_id=document.id
            )
        )

    field.field_value = new_value
    field.confidence = 1.0

    db.session.commit()

    flash("Extracted field updated successfully.", "success")

    return redirect(
        url_for(
            "documents.detail",
            document_id=document.id
        )
    )

@documents_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    document_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()

    documents_query = (
        Document.query
        .filter(Document.user_id == current_user.id)
        .outerjoin(ExtractedField)
    )

    if query:
        search_pattern = f"%{query}%"

        documents_query = documents_query.filter(
            or_(
                Document.original_filename.ilike(search_pattern),
                Document.document_type.ilike(search_pattern),
                Document.ai_summary.ilike(search_pattern),
                ExtractedField.field_name.ilike(search_pattern),
                ExtractedField.field_value.ilike(search_pattern)
            )
        )

    if document_type:
        documents_query = documents_query.filter(
            Document.document_type == document_type
        )

    if status:
        documents_query = documents_query.filter(
            Document.status == status
        )

    documents = (
        documents_query
        .distinct()
        .order_by(Document.upload_date.desc())
        .all()
    )

    document_types = (
        db.session.query(Document.document_type)
        .filter(Document.user_id == current_user.id)
        .distinct()
        .order_by(Document.document_type.asc())
        .all()
    )

    return render_template(
        "documents/search.html",
        documents=documents,
        query=query,
        selected_type=document_type,
        selected_status=status,
        document_types=[
            item[0]
            for item in document_types
            if item[0]
        ]
    )