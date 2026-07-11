from app.extensions import db


class ExtractedField(db.Model):
    __tablename__ = "extracted_fields"

    id = db.Column(db.Integer, primary_key=True)

    field_name = db.Column(
        db.String(100),
        nullable=False
    )

    field_value = db.Column(
        db.Text,
        nullable=False
    )

    confidence = db.Column(
        db.Float,
        nullable=False
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id"),
        nullable=False
    )

    document = db.relationship(
        "Document",
        back_populates="extracted_fields"
    )

    def __repr__(self):
        return f"<ExtractedField {self.field_name}>"