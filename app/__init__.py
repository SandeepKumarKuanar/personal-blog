import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "static"
)

# Ensure the upload subdirectories exist
for subdir in ["post_images", "post_covers", "temp"]:
    path = os.path.join(app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(path, exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

from app import routes, models  # keep this at bottom
