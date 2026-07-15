from flask import Blueprint


review_bp = Blueprint(
    "review",
    __name__,
    url_prefix="/review"
)


from app.review import routes