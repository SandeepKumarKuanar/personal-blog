from flask import render_template, url_for, flash, redirect
from app.forms import RegistrationForm, LoginForm, AdminLogin
from app import app


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
