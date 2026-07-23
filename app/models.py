# this is models.py
from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Association table for Posts and Tags
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


# having a user class
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(300), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(
        db.Boolean, default=False, nullable=False
    )  # add this if not present
    posts = db.relationship("Post", backref="author", lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


# having a post class
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(
        db.String(300), nullable=False, default="default.jpg"
    )  # cover image
    content = db.Column(db.Text, nullable=False)  # rendered HTML
    content_raw = db.Column(db.Text, nullable=False)  # raw Markdown
    read_time = db.Column(db.Integer, nullable=False, default=5)  # in minutes
    tags = db.relationship(
        "Tag",
        secondary=post_tags,
        backref=db.backref("posts", lazy="dynamic"),
        lazy=True,
    )

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


# having a tagging system for
# the blogs that we write
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"Tag('{self.name}')"
