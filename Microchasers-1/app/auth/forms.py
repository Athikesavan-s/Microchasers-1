from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Regexp
from app.models import User

ADMIN_CREDENTIALS = {
    'username': 'Arunnprakash',
    'password': '123',
    'email': 'arunnprakashsrivai@gmail.com'
}

def is_admin_login(username, password):
    return username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Regexp(r'^[\w.@+-]+$', message='Username can only contain letters, numbers, and . @ + - _')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Regexp(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', message='Only Gmail addresses are allowed')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', 
            message='Password must be at least 8 characters long and contain at least one letter and one number')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
