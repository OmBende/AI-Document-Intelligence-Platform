from datetime import datetime

from app.extensions import db
from app.constants import REVIEW_STATUS_PENDING, REVIEW_STATUS_REVIEWED

class ReviewQueue(db.Model):
    __tablename__ = "review_queue"

    id = db.Column(db.Integer, primary_key=True)

    field_name = db.Column(
        db.String(100),
        nullable=False
    )

    old_value = db.Column(
        db.Text,
        nullable=False
    )

    corrected_value = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
    db.String(20),
    default=REVIEW_STATUS_PENDING
)

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id"),
        nullable=False
    )

    document = db.relationship(
        "Document",
        back_populates="review_items"
    )

    def mark_reviewed(self):
        self.status = REVIEW_STATUS_REVIEWED
        self.reviewed_at = datetime.utcnow()

    def __repr__(self):
        return f"<ReviewQueue {self.field_name}>"