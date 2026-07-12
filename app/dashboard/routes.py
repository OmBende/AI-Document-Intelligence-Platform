from flask import render_template
from flask_login import current_user, login_required

from app.dashboard import dashboard_bp
from app.models import Document


@dashboard_bp.route("/")
@login_required
def index():
    documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Document.upload_date.desc()
    ).all()

    return render_template(
        "dashboard/index.html",
        documents=documents
    )