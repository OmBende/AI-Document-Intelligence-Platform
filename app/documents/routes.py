from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app.documents import documents_bp
from app.documents.forms import DocumentUploadForm
from app.documents.services import save_uploaded_document


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