# this is routes.py
import os
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app.forms import RegistrationForm, LoginForm, PostForm
from app import app, bcrypt, db
from app.models import Post, User, Tag
from app.utils import extract_zip, render_markdown
from sqlalchemy import or_
# from logging import Logger


@app.route("/")
@app.route("/home")
def main_page():
    return render_template("home.html", title="Home")


@app.route("/writings")
def blogs_page():
    # clean tags, lowercased
    tag_names = request.args.getlist("tag")
    mode = request.args.get("mode", "or").lower()

    # Base query: only published posts
    query = Post.query.filter_by(published=True)

    if tag_names:
        tag_names = [t.strip().lower() for t in tag_names if t.strip()]
        # the mode is AND operator
        if mode == "and":
            for tag_name in tag_names:
                subquery = (
                    Post.query.join(Post.tags)
                    .filter(Tag.name.ilike(tag_name))
                    .subquery()
                )
                query = query.join(subquery, Post.id == subquery.c.id)

        else:
            # OR Operator on the tag cloud
            conditions = [Tag.name.ilike(tag_name) for tag_name in tag_names]
            query = query.join(Post.tags).filter(or_(*conditions)).distinct()

    # Order by date (newest first)
    posts = query.order_by(Post.date_posted.desc()).all()

    # get all the tags of posts
    # which are published
    all_tags = Tag.query.all()

    # Add published count to each tag
    for tag in all_tags:
        tag.published_count = tag.posts.filter_by(published=True).count()

    return render_template(
        "blogs.html",
        posts=posts,
        all_tags=all_tags,
        active_tags=tag_names,
        mode=mode,
        title="Writings",
    )


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
    posts = (
        Post.query.filter_by(user_id=current_user.id)
        .order_by(Post.date_posted.desc())
        .all()
    )
    return render_template("dashboard.html", title="Accounts", posts=posts)


# we are adding new post here
@app.route("/dashboard/new-post", methods=["GET", "POST"])
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
@app.route("/writings/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    # we need to stop people from accessing the post
    # if it's not published
    if not post.published and not (
        current_user.is_authenticated and current_user.is_admin
    ):
        abort(404)
    return render_template("post.html", title=post.title, post=post)


# unpublish a published blog
@app.route("/dashboard/toggle-publish/<int:post_id>", methods=["POST"])
@login_required
def toggle_publish(post_id):
    if not current_user.is_admin:
        abort(403)

    post = Post.query.get_or_404(post_id)
    post.published = not post.published  # Toggle the status
    db.session.commit()

    status = "published" if post.published else "unpublished"
    flash(f'Post "{post.title}" has been {status}.', "success")
    return redirect(url_for("account"))


# to edit a published post
@app.route("/dashboard/edit-post/<int:post_id>", methods=["GET"])
@login_required
def edit_post(post_id):
    if not current_user.is_admin:
        abort(403)
    flash("Edit functionality coming soon!", "info")
    return redirect(url_for("account"))


# Custom error pages
# without using flask blueprints


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html", title="Page Not Found"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html", title="Forbidden"), 403


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f"Server Error: {error}")
    return render_template("errors/500.html", title="Server Error"), 500
