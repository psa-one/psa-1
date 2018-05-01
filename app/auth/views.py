from flask import render_template, redirect, request, url_for, flash, g, session
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User, Role, Parent, Student, StudentParent, School, Address, Title
from .forms import LoginForm, RegistrationForm, ParentUserRegForm, StudentParentForm, SchoolForm, PasswordResetForm, \
    PasswordResetRequestForm
from ..email import send_email
from ..decorators import admin_required


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            if current_user.is_administrator() and current_user.school is None:
                return redirect(url_for('auth.school_reg'))
            else:
                return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        school = School(school_name=form.school_name.data)
        user.school = school
        db.session.add_all([user, school])
        db.session.commit()
        login_user(user)
        send_email(user.email, 'Welcome to PSA One',
                   'auth/email/welcome_admin',
                   user=user)
        # return redirect(request.args.get('next') or url_for('auth.school_reg'))
        flash('Welcome to PSA-ONE')
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('auth/register.html', form=form)


# @auth.route('/create-school', methods=['GET', 'POST'])
# def school_reg():
#     form = SchoolForm()
#     if form.validate_on_submit():
#         school = School(school_name=form.school_name.data)
#         address = Address(address_post_code=form.school_postcode.data)
#         school.address = address
#         current_user.school = school
#         db.session.add_all([school, address, current_user])
#         db.session.commit()
#         flash('Welcome to PSA-ONE')
#         return redirect(request.args.get('next') or url_for('main.index'))
#     return render_template('auth/create_school.html', form=form)


@auth.route('/create-parent', methods=['GET', 'POST'])
@admin_required
def parent_reg():
    form1 = ParentUserRegForm()
    form1.title.choices = [(title.title_id, title.title_name) for title in Title.query.all()]
    form1.title.choices.insert(0, ('0', '-- Choose a title --'))
    if form1.validate_on_submit():
        user = User(email=form1.email.data,
                    username=form1.username.data,
                    password=form1.password.data)
        user.role = Role.query.filter_by(role_name='Parent').first()
        title = Title.query.get(form1.title.data)
        parent = Parent(
            title=title,
            first_name=form1.first_name.data,
            last_name=form1.last_name.data,
            user_id=user.id)
        user.school = current_user.school
        parent.school = current_user.school
        db.session.add_all([user, parent])
        db.session.commit()
        send_email(user.email, 'Welcome to PSA One',
                   'auth/email/welcome_parent',
                   user=user)
        session['parent_ref'] = parent.parent_id
        flash('Parent added successfully')
        return redirect(url_for('main.parent', parent_id=parent.parent_id))
    return render_template('auth/create_parent.html', form1=form1)


@auth.route('/create-parent-from-student', methods=['GET', 'POST'])
@admin_required
def create_parent_from_student():
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    form1 = ParentUserRegForm()
    form1.title.choices = [(title.title_id, title.title_name) for title in Title.query.all()]
    form1.title.choices.insert(0, ('0', '-- Choose a title --'))
    if form1.validate_on_submit():
        user = User(email=form1.email.data,
                    username=form1.username.data,
                    password=form1.password.data)
        user.role = Role.query.filter_by(role_name='Parent').first()
        title = Title.query.get(form1.title.data)
        parent = Parent(
            title=title,
            first_name=form1.first_name.data,
            last_name=form1.last_name.data,
            user_id=user.id)
        user.school = current_user.school
        parent.school = current_user.school
        parent.student.append(student)
        db.session.add_all([user, parent, student])
        db.session.commit()
        session['parent_ref'] = parent.parent_id
        flash('Parent added successfully')
        return redirect(url_for('main.student', student_id=student.student_id))
    return render_template('auth/create_parent_from_student.html', form1=form1)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


# TO BE DELETED
@auth.route("/create-parent-student", methods=['GET', 'POST'])
@login_required
@admin_required
def create_parent_student():
    parent_ref = session.get('parent_ref', None)
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    form = StudentParentForm()
    form.student.choices = [(student.student_id, student.first_name) for student in Student.query.filter_by(
        school=current_user.school).all()]
    form.student.choices.insert(0, ('0', '-- Choose a student --'))
    if form.validate_on_submit():
        parent.student.append(Student.query.get(form.student.data))
        db.session.add(parent)
        db.session.commit()
        return redirect(url_for('auth.create_parent_student', parent=parent))
    return render_template('create_parent_student.html',
                           form=form,
                           parent=parent)
