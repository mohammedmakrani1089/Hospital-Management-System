
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):

    email_or_phone = StringField(
        "Enter Your Email or Mobile Number:",
        validators=[
            DataRequired(),
            Length(max=50)
        ]
    )

    password = PasswordField(
        "Enter Your Password:",
        validators=[
            DataRequired(),
            Length(min = 6 , max=8)
        ]
    )

    submit = SubmitField("Login")
