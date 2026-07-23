# this is routes.py
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app.forms import RegistrationForm, LoginForm, AdminLogin
from app import app, bcrypt, db
from app.models import Post, User


@app.route("/")
@app.route("/home")
def main_page():
    return render_template("home.html", title="Home")


@app.route("/post")
@app.route("/posts")
@app.route("/articles")
@app.route("/blogs")
def blogs_page():
    posts = Post.query.all()
    return render_template("blogs.html", posts=posts, title="Blogs")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("blogs_page"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created for! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("blogs_page"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("Logged in Successfully!!", "success")
            return redirect(next_page) if next_page else redirect(url_for("blogs_page"))
        else:
            flash("Login unsuccessfully. Check email or password!", "danger")

    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("blogs_page"))


@app.route("/dashboard")
@login_required
def account():
    return render_template("dashboard.html", title="Accounts")


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
