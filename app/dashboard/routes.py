from collections import Counter
from datetime import datetime, timedelta

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.constants import (
    DOCUMENT_STATUS_COMPLETED,
    REVIEW_STATUS_PENDING
)
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
        1
        for document in documents
        if document.status == DOCUMENT_STATUS_COMPLETED
    )

    pending_reviews = (
        ReviewQueue.query
        .join(Document)
        .filter(
            Document.user_id == current_user.id,
            ReviewQueue.status == REVIEW_STATUS_PENDING
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


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    documents = (
        Document.query
        .filter_by(user_id=current_user.id)
        .order_by(Document.upload_date.asc())
        .all()
    )

    fields = (
        ExtractedField.query
        .join(Document)
        .filter(Document.user_id == current_user.id)
        .all()
    )

    pending_reviews = (
        ReviewQueue.query
        .join(Document)
        .filter(
            Document.user_id == current_user.id,
            ReviewQueue.status == REVIEW_STATUS_PENDING
        )
        .count()
    )

    total_documents = len(documents)

    completed_documents = sum(
        1
        for document in documents
        if document.status == DOCUMENT_STATUS_COMPLETED
    )

    average_confidence = (
        round(
            sum(field.confidence for field in fields)
            / len(fields)
            * 100
        )
        if fields
        else 0
    )

    # Documents grouped by type
    type_counter = Counter(
        document.document_type
        for document in documents
    )

    type_labels = list(type_counter.keys())
    type_values = list(type_counter.values())

    # Documents grouped by processing status
    status_counter = Counter(
        document.status
        for document in documents
    )

    status_labels = list(status_counter.keys())
    status_values = list(status_counter.values())

    # Uploads during the last seven days
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)

    upload_dates = [
        start_date + timedelta(days=offset)
        for offset in range(7)
    ]

    upload_counter = Counter(
        document.upload_date.date()
        for document in documents
        if document.upload_date
        and document.upload_date.date() >= start_date
    )

    upload_labels = [
        date.strftime("%d %b")
        for date in upload_dates
    ]

    upload_values = [
        upload_counter.get(date, 0)
        for date in upload_dates
    ]

    # Confidence distribution
    confidence_buckets = {
        "High (90–100%)": 0,
        "Medium (70–89%)": 0,
        "Low (Below 70%)": 0
    }

    for field in fields:
        confidence_percentage = field.confidence * 100

        if confidence_percentage >= 90:
            confidence_buckets["High (90–100%)"] += 1
        elif confidence_percentage >= 70:
            confidence_buckets["Medium (70–89%)"] += 1
        else:
            confidence_buckets["Low (Below 70%)"] += 1

    confidence_labels = list(confidence_buckets.keys())
    confidence_values = list(confidence_buckets.values())

    return render_template(
        "analytics/index.html",
        total_documents=total_documents,
        completed_documents=completed_documents,
        pending_reviews=pending_reviews,
        average_confidence=average_confidence,
        type_labels=type_labels,
        type_values=type_values,
        status_labels=status_labels,
        status_values=status_values,
        upload_labels=upload_labels,
        upload_values=upload_values,
        confidence_labels=confidence_labels,
        confidence_values=confidence_values
    )