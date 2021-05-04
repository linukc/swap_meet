from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Length
from wtforms.validators import regexp


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), 
                                                   regexp("^[a-zA-Z0-9]+"), 
                                                   Length(min=5)])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired(), 
                                                                   regexp("^[a-zA-Z0-9]+"), 
                                                                   Length(min=5)])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    recaptcha = RecaptchaField()
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), 
                                                   regexp("^[a-zA-Z0-9]+"),
                                                   Length(min=5)])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
