from . import db, login_manager
from datetime import datetime
from sqlalchemy_utils import PhoneNumberType
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request


class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Administrator': (0xff, True),
            'Parent': (Permission.POST_ACTIVITIES, False),
        }
        for r in roles:
            role = Role.query.filter_by(role_name=r).first()
            if role is None:
                role = Role(role_name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.role_name


class Permission:
    ADMINISTER = 0X80
    POST_ACTIVITIES = 0x01


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.school_id'))
    confirmed = db.Column(db.Boolean, default=True)
    parent = db.relationship('Parent', uselist=False, back_populates='user')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['PSA_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions == permissions)

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ADDRESS
class Address(db.Model):
    __tablename__ = 'addresses'
    address_id = db.Column(db.Integer, primary_key=True)
    address_line1 = db.Column(db.String(64))
    address_line2 = db.Column(db.String(64))
    address_city = db.Column(db.String(64))
    address_region = db.Column(db.String(64))
    address_post_code = db.Column(db.String(64))
    address_country = db.Column(db.String(64))

    parent = db.relationship('Parent', backref=db.backref('address'), lazy='dynamic')
    school = db.relationship('School', backref=db.backref('address'), lazy='dynamic')

    def __repr__(self):
        return '<Address %r>' % [self.address_line1, self.post_code]


# SCHOOL
class School(db.Model):
    __tablename__ = 'schools'
    school_id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(64), index=True)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))

    users = db.relationship('User', backref=db.backref('school'), lazy='dynamic')
    rooms = db.relationship('Room', backref=db.backref('school'), lazy='dynamic')
    students = db.relationship('Student', backref=db.backref('school'), lazy='dynamic')
    parents = db.relationship('Parent', backref=db.backref('school'), lazy='dynamic')

    def __repr__(self):
        return '<School %r>' % self.school_name


# ACTIVITY AND ACTIVITY LOG
class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, index=True, default=1001)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id'), primary_key=True)
    comment = db.Column(db.Text)
    filename = db.Column(db.String)
    creator_role = db.Column(db.String)
    private = db.Column(db.Boolean, default=False)

    students = db.relationship('Student', backref=db.backref("activity_log", cascade="all, delete-orphan"))
    activities = db.relationship('Activity', backref=db.backref("activity_log", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Activity entry %r>' % self.activities.activity_name
        # return '<Activity entry %r>' % self.timestamp


class Activity(db.Model):
    __tablename__ = 'activities'
    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(64), unique=True)

    student = db.relationship('ActivityLog',
                              backref=db.backref('activity'),
                              primaryjoin=activity_id == ActivityLog.activity_id
                              )

    @staticmethod
    def insert_activities():
        activities = {'Check-in',
                      'Check-out',
                      'Absent',
                      'Learning',
                      'Food',
                      'Nap',
                      'Potty',
                      'Kudos',
                      'Incident',
                      'Medication',
                      'Note',
                      'Photo',
                      'Video',
                      'Audio',
                      'Reminder'}
        for a in activities:
            activity = Activity.query.filter_by(activity_name=a).first()
            if activity is None:
                activity = Activity(activity_name=a)
            db.session.add(activity)
        db.session.commit()

    def __repr__(self):
        return '<Activity %r>' % self.activity_name


# STATUS AND STUDENT STATUS
class StudentStatus(db.Model):
    __tablename__ = 'student_status'
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
    status_id = db.Column(db.Integer, db.ForeignKey('status.status_id'), primary_key=True)

    students = db.relationship('Student', backref=db.backref("student_status", cascade="all, delete-orphan"))
    statuses = db.relationship('Status', backref=db.backref("student_status", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Status entry %r>' % [self.students.first_name, self.status.status_name, self.timestamp]


class Status(db.Model):
    __tablename__ = 'status'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(64), unique=True)

    student = db.relationship('StudentStatus',
                              backref=db.backref('status'),
                              primaryjoin=status_id == StudentStatus.status_id
                              )

    @staticmethod
    def insert_statuses():
        statuses = {'Lead',
                    'Toured',
                    'Applied',
                    'Waiting List',
                    'Active',
                    'Inactive',
                    'Graduated',
                    'Removed'}
        for s in statuses:
            status = Status.query.filter_by(status_name=s).first()
            if status is None:
                status = Status(status_name=s)
            db.session.add(status)
        db.session.commit()

    def __repr__(self):
        return '<Status %r>' % self.status_name


# ROOM
class Room(db.Model):
    __tablename__ = 'rooms'
    room_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.school_id'))
    room_name = db.Column(db.String(64))

    students = db.relationship('Student', backref=db.backref('room'), lazy='dynamic')

    def __repr__(self):
        return '<Room %r>' % self.room_name


# GENDER
class Gender(db.Model):
    __tablename__ = 'gender'
    gender_id = db.Column(db.Integer, primary_key=True)
    gender_name = db.Column(db.String(64), unique=True)

    students = db.relationship('Student', backref=db.backref('gender'), lazy='dynamic')

    @staticmethod
    def insert_genders():
        gender = {'Male',
                  'Female'}
        for g in gender:
            gender = Gender.query.filter_by(gender_name=g).first()
            if gender is None:
                gender = Gender(gender_name=g)
            db.session.add(gender)
        db.session.commit()

    def __repr__(self):
        return '<Gender %r>' % self.gender_name


# TITLE
class Title(db.Model):
    __tablename__ = 'title'
    title_id = db.Column(db.Integer, primary_key=True)
    title_name = db.Column(db.String(64), unique=True)

    parents = db.relationship('Parent', backref=db.backref('title'), lazy='dynamic')

    @staticmethod
    def insert_titles():
        title = {'Mr',
                 'Mrs',
                 'Miss',
                 'Ms'}
        for t in title:
            title = Title.query.filter_by(title_name=t).first()
            if title is None:
                title = Title(title_name=t)
            db.session.add(title)
        db.session.commit()

    def __repr__(self):
        return '<Title %r>' % self.title_name


# STUDENT
class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    gender_id = db.Column(db.Integer, db.ForeignKey('gender.gender_id'))
    avatar = db.Column(db.String)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    date_of_birth = db.Column(db.DateTime, index=True)
    notes = db.Column(db.Text)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.school_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))

    activity = db.relationship('ActivityLog',
                               backref=db.backref('student'),
                               primaryjoin=student_id == ActivityLog.student_id
                               )
    status = db.relationship('StudentStatus',
                             backref=db.backref('student'),
                             primaryjoin=student_id == StudentStatus.student_id
                             )
    parent = db.relationship('Parent', secondary='student_parent')

    def __repr__(self):
        return '<Student %r>' % self.first_name


# CONTACT NUMBER AND PARENT CONTACT NUMBER
class ParentContact(db.Model):
    __tablename__ = 'parent_contact'
    phone_id = db.Column(db.Integer, db.ForeignKey('contacts.contact_id'), primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'), primary_key=True)

    contact = db.relationship('Contact', backref=db.backref("parent_contact", cascade="all, delete-orphan"))
    parent = db.relationship('Parent', backref=db.backref("parent_contact", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Parent Contact entry %r>' % [self.parent.first_name, self.contact.contact]


class Contact(db.Model):
    __tablename__ = 'contacts'
    contact_id = db.Column(db.Integer, primary_key=True)
    contact = db.Column(db.String(64))
    primary_number = db.Column(db.Boolean, default=False)

    parent = db.relationship('Parent', secondary='parent_contact')

    def __repr__(self):
        return '<Contact %r>' % self.contact


# PARENT AND STUDENT PARENT
class Parent(db.Model):
    __tablename__ = 'parents'
    parent_id = db.Column(db.Integer, primary_key=True)
    title_id = db.Column(db.Integer, db.ForeignKey('title.title_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.school_id'))
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    user = db.relationship('User', uselist=False, back_populates='parent')
    student = db.relationship('Student', secondary='student_parent')
    contact = db.relationship('Contact', secondary='parent_contact')

    def __repr__(self):
        return '<Parent %r>' % self.first_name


class StudentParent(db.Model):
    __tablename__ = 'student_parent'
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'), primary_key=True)

    student = db.relationship(Student, backref=db.backref("student_parent", cascade="all, delete-orphan"))
    parent = db.relationship(Parent, backref=db.backref("student_parent", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Student Parent entry %r>' % [self.student.first_name, self.parent.first_name]
