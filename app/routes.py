# this is routes.py
import os
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app.forms import RegistrationForm, LoginForm, PostForm, EditPostForm
from app import app, bcrypt, db, posthog_client
from app.models import Post, User, Tag
from app.utils import extract_zip, render_markdown
from sqlalchemy import or_
import shutil
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

    if posthog_client:
        distinct_id = (
            str(current_user.id)
            if current_user.is_authenticated
            else request.remote_addr or "anonymous"
        )
        posthog_client.capture(
            distinct_id=distinct_id,
            event="writings_browsed",
            properties={
                "has_tag_filter": bool(tag_names),
                "tag_count": len(tag_names),
                "filter_mode": mode,
            },
        )

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

        if posthog_client:
            posthog_client.set(
                distinct_id=str(user.id),
                properties={"username": user.username, "is_admin": user.is_admin},
            )
            posthog_client.capture(
                distinct_id=str(user.id),
                event="user_registered",
                properties={"signup_method": "form"},
            )

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

            if posthog_client:
                posthog_client.set(
                    distinct_id=str(user.id),
                    properties={"username": user.username, "is_admin": user.is_admin},
                )
                posthog_client.capture(
                    distinct_id=str(user.id),
                    event="user_logged_in",
                    properties={
                        "login_method": "password",
                        "remember_me": form.remember.data,
                    },
                )

            flash("Logged in Successfully!!", "success")
            return redirect(next_page) if next_page else redirect(url_for("blogs_page"))
        else:
            flash("Login unsuccessfully. Check email or password!", "danger")

    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    if posthog_client and current_user.is_authenticated:
        posthog_client.capture(
            distinct_id=str(current_user.id), event="user_logged_out"
        )
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

    if posthog_client:
        posthog_client.capture(
            distinct_id=str(current_user.id),
            event="dashboard_viewed",
            properties={"post_count": len(posts), "is_admin": current_user.is_admin},
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

                if posthog_client:
                    posthog_client.capture(
                        distinct_id=str(current_user.id),
                        event="post_created",
                        properties={
                            "tag_count": len(post.tags),
                            "has_cover_image": bool(form.cover_image.data),
                            "read_time": post.read_time,
                        },
                    )

                flash("Post published successfully!", "success")
                return redirect(url_for("post_detail", post_id=post.id))

            except Exception as e:
                db.session.rollback()
                if posthog_client:
                    posthog_client.capture_exception(e)
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

    if posthog_client:
        distinct_id = (
            str(current_user.id)
            if current_user.is_authenticated
            else request.remote_addr or "anonymous"
        )
        posthog_client.capture(
            distinct_id=distinct_id,
            event="post_viewed",
            properties={
                "post_id": post.id,
                "is_published": post.published,
                "read_time": post.read_time,
            },
        )

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

    if posthog_client:
        posthog_client.capture(
            distinct_id=str(current_user.id),
            event="post_visibility_toggled",
            properties={"post_id": post.id, "is_now_published": post.published},
        )

    status = "published" if post.published else "unpublished"
    flash(f'Post "{post.title}" has been {status}.', "success")
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


@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")


@app.route("/dashboard/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    if not current_user.is_admin:
        abort(403)

    post = Post.query.get_or_404(post_id)
    form = EditPostForm()
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]

    if form.validate_on_submit():
        post.title = form.title.data
        post.content_raw = form.content.data
        post.content = render_markdown(form.content.data)  # Re‑render
        post.read_time = form.read_time.data
        post.date_posted = form.date_posted.data
        post.tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for("post_detail", post_id=post.id))

    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content_raw
        form.read_time.data = post.read_time
        form.date_posted.data = post.date_posted.date()
        form.tags.data = [tag.id for tag in post.tags]

    return render_template("edit_post.html", title="Edit Post", form=form, post=post)


@app.route("/dashboard/delete-post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        abort(403)

    post = Post.query.get_or_404(post_id)
    post_title = post.title

    # 1. Delete the post_images folder for this post (if it exists)
    post_images_dir = os.path.join(
        app.config["UPLOAD_FOLDER"], "post_images", str(post_id)
    )
    if os.path.exists(post_images_dir):
        shutil.rmtree(post_images_dir)

    # 2. Delete the cover image (if it's not the default)
    if post.image_file and "default.jpg" not in post.image_file:
        cover_path = os.path.join(app.config["UPLOAD_FOLDER"], post.image_file)
        if os.path.exists(cover_path):
            os.remove(cover_path)

    # 3. Delete the post from the database
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post_title}" has been deleted.', "success")
    return redirect(url_for("account"))
    # cleans the entire canvas and removes the post
