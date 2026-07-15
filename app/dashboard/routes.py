from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.dashboard import dashboard_bp
from app.extensions import db
from app.models import Document, ExtractedField, ReviewQueue


@dashboard_bp.route("/")
@login_required
def index():
    documents = (
        Document.query
        .filter_by(user_id=current_user.id)
        .order_by(Document.upload_date.desc())
        .all()
    )

    total_documents = len(documents)

    completed_documents = sum(
        1 for document in documents
        if document.status == "Completed"
    )

    pending_reviews = (
        ReviewQueue.query
        .join(Document)
        .filter(
            Document.user_id == current_user.id,
            ReviewQueue.status == "Pending"
        )
        .count()
    )

    average_confidence_value = (
        db.session.query(func.avg(ExtractedField.confidence))
        .join(Document)
        .filter(Document.user_id == current_user.id)
        .scalar()
    )

    average_confidence = (
        round(average_confidence_value * 100)
        if average_confidence_value
        else 0
    )

    return render_template(
        "dashboard/index.html",
        documents=documents,
        total_documents=total_documents,
        completed_documents=completed_documents,
        pending_reviews=pending_reviews,
        average_confidence=average_confidence
    )