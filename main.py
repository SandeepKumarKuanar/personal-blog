from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm, AdminLogin
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# adding a secret key to make my site
# somewhat secure
app.config["SECRET_KEY"] = "07315b38258dc4a63b758ed311da3b71"

# adding the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
db = SQLAlchemy(app)
# Association table for Posts and Tags
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


# having a user class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(300), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship("Post", backref="author", lazy=True)

    def __repr__(self) -> str:
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# having a post class
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking to User.id
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(300), unique=True, nullable=False)  # Fixed length
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(300), nullable=False, default="default.jpg")
    content = db.Column(db.Text, nullable=False)

    def __repr__(self) -> str:
        return f"Post('{self.title}', '{self.date_posted}')"


# having a tagging system for
# the blogs that we write
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Tag('{self.name}')"


@app.route("/")
@app.route("/home")
def main_page():
    return render_template("home.html", title="Home")


@app.route("/post")
@app.route("/posts")
@app.route("/articles")
@app.route("/blogs")
def blogs_page():
    return render_template("blogs.html", posts=posts, title="Blogs")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("blogs_page"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash("Logged in Successfully!!", "success")
        return redirect(url_for("blogs_page"))
    else:
        flash("Incorrect username or password!", "danger")
        return render_template("login.html", title="Login", form=form)


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    form = AdminLogin()
    if (
        form.validate_on_submit()
        and form.email.data == "admin@blog.com"
        and form.password.data == "password"
    ):
        flash("Logged in as ADMIN Successfully!!", "success")
        return redirect(url_for("blogs_page"))
    else:
        flash("Incorrect username or password!", "danger")

    return render_template("adminLogin.html", title="Admin login", form=form)


if __name__ == "__main__":
    app.run(debug=True)
