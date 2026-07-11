from datetime import datetime

from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    document_type = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Uploaded"
    )

    upload_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="documents"
    )

    extracted_fields = db.relationship(
        "ExtractedField",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    review_items = db.relationship(
        "ReviewQueue",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document {self.original_filename}>"