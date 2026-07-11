from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class DocumentUploadForm(FlaskForm):
    document = FileField(
        "Choose Document",
        validators=[
            FileRequired(),
            FileAllowed(
                ["pdf", "docx", "jpg", "jpeg", "png"],
                "Only PDF, DOCX, JPG, JPEG, and PNG files are allowed."
            )
        ]
    )

    document_type = SelectField(
        "Document Type",
        choices=[
            ("Resume", "Resume"),
            ("Invoice", "Invoice"),
            ("Contract", "Contract"),
            ("Certificate", "Certificate"),
            ("Form", "Form"),
            ("Other", "Other")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Upload Document")