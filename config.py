import os

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


class Config:
    """
    Base configuration class.
    All application settings are stored here.
    """

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH"))