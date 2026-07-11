from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate
from app.models import User, Document, ExtractedField, ReviewQueue


def create_app():
    """
    Application Factory Function.
    Creates and configures the Flask application.
    """

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return "Welcome to AI Document Intelligence Platform!"

    return app