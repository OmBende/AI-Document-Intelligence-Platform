from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Document, ExtractedField, ReviewQueue
from app.review import review_bp


@review_bp.route("/")
@login_required
def index():
    review_items = (
        ReviewQueue.query
        .join(Document)
        .filter(
            Document.user_id == current_user.id,
            ReviewQueue.status == "Pending"
        )
        .order_by(ReviewQueue.id.desc())
        .all()
    )

    return render_template(
        "review/index.html",
        review_items=review_items
    )


@review_bp.route("/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit(review_id):
    review_item = (
        ReviewQueue.query
        .join(Document)
        .filter(
            ReviewQueue.id == review_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if review_item is None:
        abort(404)

    if request.method == "POST":
        corrected_value = request.form.get(
            "corrected_value",
            ""
        ).strip()

        review_item.corrected_value = corrected_value
        review_item.mark_reviewed()

        extracted_field = ExtractedField.query.filter_by(
            document_id=review_item.document_id,
            field_name=review_item.field_name
        ).first()

        if extracted_field:
            extracted_field.field_value = corrected_value
            extracted_field.confidence = 1.0

        db.session.commit()

        flash(
            "Field reviewed and updated successfully.",
            "success"
        )

        return redirect(url_for("review.index"))

    return render_template(
        "review/edit.html",
        review_item=review_item
    )