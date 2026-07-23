# this is routes.py
import os
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app.forms import RegistrationForm, LoginForm, AdminLogin, PostForm
from app import app, bcrypt, db
from app.models import Post, User, Tag
from app.utils import extract_zip, render_markdown


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


# we are adding new post here
@app.route("/admin/new-post", methods=["GET", "POST"])
@login_required
def new_post():
    if not current_user.is_admin:
        abort(403)
    form = PostForm()
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]

    if form.validate_on_submit():
        zip_file = form.zip_file.data
        if zip_file:
            try:
                # Create post first to get ID
                post = Post(
                    title="Temporary",  # Will be updated
                    content_raw="",  # Will be updated
                    content="",  # Will be updated
                    user_id=current_user.id,
                    image_file="default.jpg",
                    read_time=form.read_time.data,
                )
                db.session.add(post)
                db.session.flush()
                post_id = post.id

                # Process ZIP with actual post_id
                zip_file.seek(0)
                title, content_raw, image_filenames = extract_zip(zip_file, post_id)
                post.title = title
                post.content_raw = content_raw
                post.content = render_markdown(content_raw)

                # Save cover image
                if form.cover_image.data:
                    cover_filename = secure_filename(form.cover_image.data.filename)
                    cover_path = os.path.join(
                        app.config["UPLOAD_FOLDER"], "post_covers", str(post_id)
                    )
                    os.makedirs(cover_path, exist_ok=True)
                    cover_filepath = os.path.join(cover_path, cover_filename)
                    form.cover_image.data.save(cover_filepath)
                    post.image_file = f"post_covers/{post_id}/{cover_filename}"

                # Save tags
                post.tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()

                db.session.commit()
                flash("Post published successfully!", "success")
                return redirect(url_for("post_detail", post_id=post.id))

            except Exception as e:
                db.session.rollback()
                flash(f"Error processing ZIP: {str(e)}", "danger")
                return render_template("admin_new_post.html", form=form)
        else:
            flash("Please upload a ZIP file.", "danger")
            return render_template("admin_new_post.html", form=form)

    return render_template("admin_new_post.html", form=form)


# we are viewing the post
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)
