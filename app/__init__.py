import atexit
import os

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from posthog import Posthog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
# Get the directory where this __init__.py file is located (app/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),  # app/static/
    static_url_path="/static",
)

app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASE_DIR, '..', 'instance', 'site.db')}"
)
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static")  # app/static/

# Ensure the upload subdirectories exist inside app/static/
for subdir in ["post_images", "post_covers", "temp"]:
    path = os.path.join(app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(path, exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

_posthog_token = os.environ.get("POSTHOG_PROJECT_TOKEN")
_posthog_host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")

if _posthog_token:
    posthog_client = Posthog(
        project_api_key=_posthog_token,
        host=_posthog_host,
        enable_exception_autocapture=True,
        debug=app.debug,
    )
    atexit.register(posthog_client.shutdown)
else:
    posthog_client = None
    if app.debug:
        raise RuntimeError(
            "POSTHOG_PROJECT_TOKEN variable required by PostHog is missing or "
            "un-configured, this causes events to be silently missed. "
            "This error stops appearing once POSTHOG_PROJECT_TOKEN is configured"
        )

from app import routes, models  # keep this at bottom
