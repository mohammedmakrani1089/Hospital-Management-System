# from flask_wtf import FlaskForm
# from wtforms import PasswordField, StringField, SubmitField
# from wtforms.validators import Length, DataRequired,Email , EqualTo

# class SignUpForm(FlaskForm):
    
#     username = StringField("Enter Your Username :- " , validators = [DataRequired()])
#     email = StringField("Enter Your Email :- " , validators = [DataRequired(), Email()] )
#     password = PasswordField("Create Your Password :- ", validators = [DataRequired(), Length( min = 6)])
#     confirm_password = PasswordField("Re-Enter Your Password :- ", validators = [DataRequired(), Length( min = 6), EqualTo("password")])
#     submit = SubmitField("SignUp")

from flask_wtf import FlaskForm
from wtforms import PasswordField , StringField , SubmitField , SelectField , DateField , FileField 
from wtforms.validators import Length, Email , DataRequired , EqualTo , Regexp 
from flask_wtf.file import FileAllowed

class SignUpForm(FlaskForm):
    full_name = StringField("Enter Your Full Name :- " , validators=[DataRequired() , Length(min=4 , max=100 )])
    email = StringField("Enter Your Email :- " , validators=[DataRequired(), Email(), Length(max=50)])
    phone_no = StringField("Enter Your Mobile No :-", validators=[DataRequired(), Length(min=10 , max=10), Regexp(r'^[0-9]{10}$', message="Enter Valid 10 digit Number.")])
    gender = SelectField("Select Your Gender :-" , choices= [("", "Select Gender"),("Male", "Male"),("Female", "Female"),("Other", "Other")] , validators=[DataRequired()])
    date_of_birth = DateField("Enter Your Date of Birth:- ", format="%Y-%m-%d",validators=[DataRequired()])
    profile_image = FileField("Upload Profile Picture:- ",validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'],"Only JPG, PNG and WEBP images are allowed.")])
    password = PasswordField("Create Your Password :- ", validators = [DataRequired(), Length(min = 6 , max=8)])
    confirm_password = PasswordField("Re-Enter Your Password :- ", validators = [DataRequired(), Length(min = 6 , max=8), EqualTo("password",  message="Passwords must match.")])
    submit = SubmitField("SignUp")  
    
    
    