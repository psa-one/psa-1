from flask_wtf import Form
from wtforms.fields.html5 import DateField, DateTimeLocalField
from wtforms_components import TimeField
from wtforms_alchemy import PhoneNumberField
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileStorage
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import Room, Student, Status, StudentStatus, Role, User
from flask_login import current_user
from .. import db, photos, audio
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, DateTimeField, \
    PasswordField, SelectMultipleField, MultiCheckboxField


class RoomForm(Form):
    room_name = StringField('Room name', validators=[DataRequired()])
    submit = SubmitField('Add room')


class UpdateRoomForm(Form):
    room_name = StringField('Room name', validators=[DataRequired()])
    submit2 = SubmitField('Update room name')


class EditProfileForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[
                               DataRequired(),
                               Length(1, 64),
                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                      'Usernames must have only letters, numbers, dots or underscores')])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        if field.data != current_user.email:
            user = User.query.filter_by(email=field.data).first()
            if user is not None:
                raise ValueError('{} is already registered.'.format(field.data))

    def validate_username(self, field):
        if field.data != current_user.username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValueError('{} is already taken.'.format(field.data))


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username',
                           validators=[
                               DataRequired(),
                               Length(1, 64),
                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                      'Usernames must have only letters, numbers, dots or underscores')])
    # role = SelectField('Permissions', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email:
            user = User.query.filter_by(email=field.data).first()
            if user is not None:
                raise ValueError('{} is already registered.'.format(field.data))

    def validate_username(self, field):
        if field.data != self.user.username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValueError('{} is already taken.'.format(field.data))


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired()])
    submit = SubmitField('Update Password')


class StudentForm(Form):
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    gender = SelectField('Gender', coerce=int)
    date_of_birth = DateField('Date of birth')
    status = SelectField('Status', coerce=int)
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class AvatarForm(Form):
    avatar = FileField('Profile picture', validators=[
        FileRequired(),
        FileAllowed(photos, 'Images only')])
    submit = SubmitField('Submit')


# ADDS A STUDENT TO A ROOM FROM THE ROOM'S PAGE
class RoomStudentForm(Form):
    student = SelectField('Student', coerce=int)
    submit = SubmitField('Add student')


# ADDS A STUDENT TO A ROOM FROM THE STUDENT'S PAGE
class StudentRoomForm(Form):
    room = SelectField('', coerce=int)
    submit = SubmitField('Submit')


# ADDS A PARENT TO A STUDENT
class ParentStudentForm(Form):
    parent = SelectField('', coerce=int)
    submit2 = SubmitField('Submit')


# ACTIVITY FORMS
class ActivityForm(Form):
    activity = SelectField('Add activity', coerce=int)
    submit3 = SubmitField('Continue')


class AbsentActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class AudioActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    upload = FileField('Audio', validators=[FileRequired()])
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class CheckinActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class CheckoutActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class FoodActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class IncidentActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (required)', validators=[DataRequired()])
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class KudosActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class LearningActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class MedicationActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class NapActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class NoteActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (required)', validators=[DataRequired()])
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class PhotoActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    upload = FileField('Photo', validators=[FileRequired(), FileAllowed(photos, 'Images only')])
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class PottyActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class ReminderActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    comment = TextAreaField('Comment (required)', validators=[DataRequired()])
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')


class VideoActivityForm(Form):
    activity_date = DateField('Date')
    activity_time = TimeField('Time')
    upload = FileField('Video', validators=[FileRequired()])
    comment = TextAreaField('Comment (optional)')
    privacy = BooleanField('Private', default=False)
    submit = SubmitField('Submit')
# END OF ACTIVITY FORMS


class ContactNumberForm(Form):
    contact_number = StringField("", validators=[DataRequired()])
    primary_number = BooleanField('Primary Number', default=False)
    submit2 = SubmitField('Submit')


class EditContactNumberForm(Form):
    contact_number = StringField("", validators=[DataRequired()])
    primary_number = BooleanField('Primary Number', default=False)
    submit3 = SubmitField('Submit')


class AddressForm(Form):
    address_line1 = StringField("Address 1")
    address_line2 = StringField("Address 2")
    address_city = StringField("City")
    address_region = StringField("Region")
    address_post_code = StringField("Post Code / Area Code")
    address_country = StringField("Country")
    submit = SubmitField('Submit')


class SchoolNameForm(Form):
    school_name = StringField("School Name")
    submit = SubmitField('Submit')


class UploadTestForm(Form):
    timestamp1 = DateTimeField('WTForms DateTimeField')
    comment = TextAreaField('Comment (optional)')
    submit = SubmitField('Submit')


class GroupActivityForm(Form):
    activity = SelectField('Choose activity', coerce=int)
    students = MultiCheckboxField('Students', coerce=int)
    # students = SelectMultipleField('Students', coerce=int)
    submit = SubmitField('Next: Step 3 - Activity Detail')
