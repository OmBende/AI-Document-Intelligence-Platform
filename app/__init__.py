from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate
from app.models import User, Document, ExtractedField, ReviewQueue


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

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def home():
        return "Welcome to AI Document Intelligence Platform!"

    return app