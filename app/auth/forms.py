from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo
from ..models import Room, Student, Status, Role, User, StudentStatus


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me signed in')
    submit = SubmitField('Sign In')


class RegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[
                               DataRequired(),
                               Length(1, 64),
                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                      'Usernames must have only letters, numbers, dots or underscores')
                           ])
    school_name = StringField('School name', validators=[DataRequired()])
    password = PasswordField('Password',
                             validators=[
                                 DataRequired(),
                                 EqualTo('password2', message='Passwords must match')
                             ])
    password2 = PasswordField('Confirm Password',
                              validators=[
                                 DataRequired(),
                              ])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email address already in use')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')


class SchoolForm(Form):
    school_name = StringField('School name', validators=[DataRequired()])
    school_postcode = StringField('Post code', validators=[DataRequired()])
    submit = SubmitField('Add School')


class ParentUserRegForm(Form):
    title = SelectField('Title', coerce=int)
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[
                               DataRequired(),
                               Length(1, 64),
                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                      'Usernames must have only letters, numbers, dots or underscores')
                           ])
    password = PasswordField('Password',
                             validators=[
                                 DataRequired(),
                                 EqualTo('password2', message='Passwords must match')
                             ])
    password2 = PasswordField('Confirm Password',
                              validators=[
                                 DataRequired(),
                              ])
    submit = SubmitField('Add Parent')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email address already in use')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


# ADDS A STUDENT TO A PARENT FROM THE PARENT'S PAGE
class StudentParentForm(Form):
    student = SelectField('', coerce=int)
    submit = SubmitField('Submit')
