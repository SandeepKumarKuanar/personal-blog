# app/utils.py
import os
import zipfile
import re
import markdown2

# from werkzeug.utils import secure_filename
from flask import current_app


def extract_zip(zip_file, post_id):
    """
    Extract zip file, read .md, rewrite image paths, return (title, content_raw, image_filenames)
    """
    # Create temporary directory for extraction
    temp_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp", str(post_id))
    os.makedirs(temp_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(temp_dir)

        # Find the .md file (there should be exactly one)
        md_files = [f for f in os.listdir(temp_dir) if f.endswith(".md")]
        if len(md_files) != 1:
            raise ValueError("ZIP must contain exactly one .md file.")
        md_filename = md_files[0]
        md_path = os.path.join(temp_dir, md_filename)

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Parse title (first line starting with '# ')
        lines = md_content.splitlines()
        title = None
        content_lines = []
        for line in lines:
            if title is None and line.startswith("# "):
                title = line[2:].strip()
            else:
                content_lines.append(line)
        if title is None:
            raise ValueError("No title found (first line starting with '# ').")
        content_raw = "\n".join(content_lines)

        # Collect images in the zip root (no subfolders)
        image_filenames = []
        for filename in os.listdir(temp_dir):
            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
            ):
                image_filenames.append(filename)

        # Rewrite image paths in content_raw
        # I want to replace patterns like ![alt](filename) with /static/post_images/<post_id>/filename
        # Also handled./filename and ../filename
        for img in image_filenames:
            # pattern: ![alt](some/path/filename) or ![alt](filename)
            # I want to replace with /static/post_images/<post_id>/filename
            # Keep absolute URLs untouched.
            pattern = r"(!\[.*?\]\()(.*?)(" + re.escape(img) + r")(\))"

            def repl(match):
                prefix = match.group(1)
                path = match.group(2)
                suffix = match.group(4)
                # If path starts with http:// or https:// or /, leave as is
                if path.startswith(("http://", "https://", "/")):
                    return match.group(0)
                # Otherwise rewrite
                new_path = f"/static/post_images/{post_id}/{img}"
                return prefix + new_path + suffix

            content_raw = re.sub(pattern, repl, content_raw)

        return title, content_raw, image_filenames
    finally:
        # Clean up temp directory
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def render_markdown(md_content):
    """Convert Markdown to HTML using markdown2 with fenced code blocks."""
    return markdown2.markdown(
        md_content, extras=["fenced-code-blocks", "tables", "header-ids"]
    )
