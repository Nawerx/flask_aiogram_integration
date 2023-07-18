from wtforms import StringField, PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired,  Length, EqualTo

class Register_form(FlaskForm):
    username = StringField("Username: ", validators=[Length(min=4, max=64), DataRequired()])
    password = PasswordField("Password: ", validators=[Length(min=4, max=32), DataRequired()])
    password_rep = PasswordField("Repeat Password: ", validators=[EqualTo("password", message="Паролі не співпадають"), DataRequired()])

class Login_form(FlaskForm):
    username = StringField("Username: ", validators=[Length(min=4, max=64)])
    password = PasswordField("Password: ", validators=[Length(min=4, max=32)])

class Create_Note_Form(FlaskForm):
    title = StringField("Title: ", validators=[Length(min=1, max=64)])
    content = StringField("Content: ", validators=[DataRequired()])

