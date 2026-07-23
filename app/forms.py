# a place where every form has it's own place
# this is forms.py
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    BooleanField,
    StringField,
    PasswordField,
    SubmitField,
    ValidationError,
    TextAreaField,
    IntegerField,
    SelectMultipleField,
)

from app.models import User, Tag


class AdminLogin(FlaskForm):
    email = StringField("Admin email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login as Admin")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Your name", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Your email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign up")

    # we going to have safeguards to not have
    # the same username or password
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("This username is taken. Please choose another one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("This email is taken. Please choose another one.")


class LoginForm(FlaskForm):
    email = StringField("Your email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login in")


class PostForm(FlaskForm):
    zip_file = FileField(
        "Upload Blog ZIP (contains .md and images)",
        validators=[FileAllowed(["zip"], "ZIP files only!")],
    )
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content (Markdown)", validators=[DataRequired()])
    cover_image = FileField(
        "Cover Photo",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "png", "jpeg", "gif", "webp"], "Images only!"),
        ],
    )
    read_time = IntegerField(
        "Estimated Read Time (minutes)", validators=[DataRequired()], default=5
    )
    tags = SelectMultipleField("Tags", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Publish")

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
