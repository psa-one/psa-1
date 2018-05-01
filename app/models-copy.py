from . import db, login_manager
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
import hashlib


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
            'User': (Permission.FOLLOW |
            Permission.COMMENT |
            Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
            Permission.COMMENT |
            Permission.WRITE_ARTICLES |
            Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
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
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column
    # posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['PSA_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

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
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar/'
        else:
            url = 'https://www.gravatar.com/avatar/'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

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


# STUDENT, STATUS AND STUDENT STATUS
class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), unique=True)

    status = db.relationship('Status', secondary='student_status')
    room = db.relationship('Room', secondary='room_allocation')
    activity = db.relationship('Activity', secondary='activity_log')
    parent = db.relationship('Parent', secondary='student_parent')

    def __repr__(self):
        return '<Student %r>' % self.first_name


class Status(db.Model):
    __tablename__ = 'status'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(64), unique=True)

    student = db.relationship('Student', secondary='student_status')

    def __repr__(self):
        return '<Status %r>' % self.status_name


class StudentStatus(db.Model):
    __tablename__ = 'student_status'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    status_id = db.Column(db.Integer, db.ForeignKey('status.status_id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    student = db.relationship(Student, backref=db.backref("student_status", cascade="all, delete-orphan"))
    status = db.relationship(Status, backref=db.backref("student_status", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Status timestamp %r>' % self.timestamp


# ROOM AND ROOM ALLOCATIONS
class Room(db.Model):
    __tablename__ = 'rooms'
    room_id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(64), unique=True)

    student = db.relationship('Student', secondary='room_allocation')

    def __repr__(self):
        return '<Room %r>' % self.room_name


class RoomAllocation(db.Model):
    __tablename__ = 'room_allocation'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    student = db.relationship(Student, backref=db.backref("room_allocation", cascade="all, delete-orphan"))
    room = db.relationship(Room, backref=db.backref("room_allocation", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Room timestamp %r>' % self.timestamp


# ACTIVITY AND ACTIVITY LOG
class Activity(db.Model):
    __tablename__ = 'activities'
    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(64), unique=True)

    student = db.relationship('Student', secondary='activity_log')

    def __repr__(self):
        return '<Activity %r>' % self.activity_name


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id'), primary_key=True)
    # timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    # activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id'))
    # __table_args__ = (PrimaryKeyConstraint('timestamp', 'student_id', 'activity_id'), {})

    student = db.relationship(Student, backref=db.backref("activity_log", cascade="all, delete-orphan"))
    activity = db.relationship(Activity, backref=db.backref("activity_log", cascade="all, delete-orphan"))

    def __repr__(self):
        return '<Activity entry %r>' % [self.student.first_name, self.activity.activity_name, self.timestamp]


# PARENT AND STUDENT PARENT
class Parent(db.Model):
    __tablename__ = 'parents'
    parent_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), unique=True)

    student = db.relationship('Student', secondary='student_parent')

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
