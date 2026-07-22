from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm, AdminLogin

app = Flask(__name__)
# adding a secret key to make my site
# somewhat secure

app.config["SECRET_KEY"] = "07315b38258dc4a63b758ed311da3b71"

# assume that this are my posts, which
# I receive when I do a database call
posts = [
    {
        "author": "Sandeep Kumar Kuanar",
        "title": "Blog post 1",
        "content": "first post content",
        "date_posted": "July 20, 2026",
    },
    {
        "author": "Sandeep Kumar Kuanar",
        "title": "Blog post 2",
        "content": "second post content",
        "date_posted": "July 21, 2026",
    },
]


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
