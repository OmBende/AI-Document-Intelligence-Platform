from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from app.extensions import db, login_manager, migrate
from app.models import User, Document, ReviewQueue


def create_app():
    """
    Creates and configures the Flask application.
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.documents import documents_bp
    app.register_blueprint(documents_bp)

    from app.review import review_bp
    app.register_blueprint(review_bp)

    # Make pending review count available in all templates
    @app.context_processor
    def inject_review_count():
        if not current_user.is_authenticated:
            return {"pending_review_count": 0}

        pending_review_count = (
            ReviewQueue.query
            .join(Document)
            .filter(
                Document.user_id == current_user.id,
                ReviewQueue.status == "Pending"
            )
            .count()
        )

        return {
            "pending_review_count": pending_review_count
        }

    # Home route
    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))

        return redirect(url_for("auth.login"))

    return app