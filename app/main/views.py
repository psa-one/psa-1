from flask import render_template, session, redirect, url_for, flash, abort, request, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime
from . import main
from .forms import RoomForm, EditProfileForm, EditProfileAdminForm, StudentForm, RoomStudentForm, \
    StudentRoomForm, ParentStudentForm, ActivityForm, AbsentActivityForm, AudioActivityForm, CheckinActivityForm, \
    CheckoutActivityForm, FoodActivityForm, IncidentActivityForm, KudosActivityForm, LearningActivityForm, \
    MedicationActivityForm, NapActivityForm, NoteActivityForm, PhotoActivityForm, PottyActivityForm, \
    ReminderActivityForm, VideoActivityForm, ContactNumberForm, AddressForm, SchoolNameForm, UploadTestForm, \
    AvatarForm, UpdateRoomForm, EditContactNumberForm, ChangePasswordForm, GroupActivityForm, \
    GeneralActivityForm, RequiredCommentActivityForm, Audio2ActivityForm, Photo2ActivityForm, Video2ActivityForm
from ..auth.forms import StudentParentForm
from .. import db, photos, videos, audio
from ..models import Room, School, Student, Status, Role, User, StudentStatus, Permission, Parent, StudentParent, \
    Activity, ActivityLog, Contact, Address, Gender, ParentContact
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename
import os, json, boto3


@main.route("/", methods=['GET', 'POST'])
@login_required
def index():
    rooms = Room.query.filter_by(school=current_user.school).count()
    students = Student.query.filter_by(school=current_user.school).count()
    parents = Parent.query.filter_by(school=current_user.school).count()
    parent = Parent.query.filter_by(user_id=current_user.id).first()
    return render_template('index.html', rooms=rooms, students=students, parents=parents, parent=parent)


@main.route("/rooms", methods=['GET', 'POST'])
@login_required
@admin_required
def rooms():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(room_name=form.room_name.data)
        room.school = current_user.school
        db.session.add(room)
        return redirect(url_for('.rooms'))
    rooms = Room.query.filter_by(school=current_user.school).all()
    return render_template('rooms.html',
                           form=form,
                           room_name=form.room_name.data,
                           rooms=rooms)


@main.route("/room/<room_id>", methods=['GET', 'POST'])
@login_required
@admin_required
def room(room_id):
    room = Room.query.filter_by(room_id=room_id).first()
    form = RoomStudentForm()
    form2 = UpdateRoomForm()
    form.student.choices = [(student.student_id,
                             # [student.first_name, student.last_name]
                             student.last_name+', '+student.first_name
                             )
                            for student in Student.query.filter_by(
        school=current_user.school).all()]
    form.student.choices.insert(0, ('0', '-- Choose a student --'))
    session['room_ref'] = room.room_id
    if form.submit.data and form.validate():
        student = Student.query.get(form.student.data)
        student.room = room
        db.session.commit()
        return redirect(url_for('.room', room_id=room.room_id))
    if form2.submit2.data and form2.validate():
        room.room_name = form2.room_name.data
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('.room', room_id=room.room_id))
    if room is None:
        abort(404)
    if room.school == current_user.school:
        form2.room_name.data = room.room_name
        return render_template('room.html', room=room, form=form, form2=form2)
    else:
        abort(404)


@main.route("/delete-room", methods=['GET', 'POST'])
@login_required
@admin_required
def delete_room():
    room_ref = session.get('room_ref', None)
    room = Room.query.filter_by(room_id=room_ref).first()
    db.session.delete(room)
    db.session.commit()
    flash('Room successfully deleted')
    return redirect(url_for('main.rooms'))


@main.route("/students")
@login_required
@admin_required
def students():
    students = Student.query.filter_by(school=current_user.school).all()
    return render_template('students.html', students=students)


@main.route("/student/<student_id>", methods=['GET', 'POST'])
@login_required
def student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    form = StudentRoomForm(student=student)
    parent_form = ParentStudentForm()
    activity_form = ActivityForm()
    form.room.choices = [(room.room_id, room.room_name) for room in Room.query.filter_by(
        school=current_user.school).all()]
    form.room.choices.insert(0, ('0', '-- Choose a room --'))
    parent_form.parent.choices = [(parent.parent_id,
                                   parent.last_name + ', ' + parent.first_name
                                   ) for parent in Parent.query.filter_by(
        school=current_user.school).all()]
    parent_form.parent.choices.insert(0, ('0', '-- Choose a parent --'))
    activity_form.activity.choices = [(activity.activity_id, activity.activity_name) for activity
                                      in Activity.query.order_by(Activity.activity_name).all()]
    activity_form.activity.choices.insert(0, ('0', '-- Choose an activity --'))
    session['student_ref'] = student.student_id
    if activity_form.submit3.data and activity_form.validate():
        chosen_activity = Activity.query.get(activity_form.activity.data)
        session['chosen_activity_id'] = chosen_activity.activity_id
        return redirect(url_for('main.activity_detail'))
    if form.submit.data and form.validate():
        student.room = Room.query.get(form.room.data)
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('main.student', student_id=student.student_id))
    if parent_form.submit2.data and parent_form.validate():
        student.parent.append(Parent.query.get(parent_form.parent.data))
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('main.student', student_id=student.student_id))
    if student is None:
        abort(404)
    if student.school == current_user.school and current_user.is_administrator() or \
            current_user.parent in student.parent:
        active_tab = ''
        if True:
            active_tab = request.cookies.get('active_tab', '')
        activity_log = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).all()
        student_status = StudentStatus.query.filter_by(
            students=student).order_by(StudentStatus.timestamp.desc()).first()
        return render_template('student.html', student=student,
                               active_tab=active_tab,
                               form=form, parent_form=parent_form, activity_form=activity_form,
                               activity_log=activity_log, student_status=student_status)
    else:
        abort(404)


@main.route("/student/school")
@login_required
def show_school():
    student_ref = session.get('student_ref', None)
    student_id = student_ref
    resp = make_response(redirect(url_for('main.student', student_id=student_id)))
    resp.set_cookie('active_tab', '1'
                    )
    return resp


@main.route("/student/home")
@login_required
def show_home():
    student_ref = session.get('student_ref', None)
    student_id = student_ref
    resp = make_response(redirect(url_for('main.student', student_id=student_id)))
    resp.set_cookie('active_tab', '2'
                    )
    return resp


@main.route("/student/all")
@login_required
def show_all():
    student_ref = session.get('student_ref', None)
    student_id = student_ref
    resp = make_response(redirect(url_for('main.student', student_id=student_id)))
    resp.set_cookie('active_tab', '3'
                    )
    return resp


@main.route("/student/profile")
@login_required
def show_profile():
    student_ref = session.get('student_ref', None)
    student_id = student_ref
    resp = make_response(redirect(url_for('main.student', student_id=student_id)))
    resp.set_cookie('active_tab', '4'
                    )
    return resp


@main.route("/activity-detail", methods=['GET', 'POST'])
@login_required
def activity_detail():
    chosen_activity_id = session.get('chosen_activity_id', None)
    activity = Activity.query.filter_by(activity_id=chosen_activity_id).first()
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    id_inc = 1001
    # ACTIVITY CREATION
    if activity.activity_name == 'Audio':
        form = Audio2ActivityForm()
    elif activity.activity_name == 'Photo':
        form = Photo2ActivityForm()
    elif activity.activity_name == 'Video':
        form = Video2ActivityForm()
    elif activity.activity_name == 'Incident' or \
            activity.activity_name == 'Note' or \
            activity.activity_name == 'Reminder':
        form = RequiredCommentActivityForm()
    else:
        form = GeneralActivityForm()
    if form.validate_on_submit():
        activity_date = form.activity_date.data
        activity_time = form.activity_time.data
        activity_datetime = datetime.combine(activity_date, activity_time)
        comment = form.comment.data
        private = form.privacy.data
        if ActivityLog.query.filter_by(students=student).all():
            last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
            id_inc = last.id + 1
        activity_entry = ActivityLog(id=id_inc,
                                     timestamp=activity_datetime,
                                     student_id=student.student_id,
                                     activity_id=activity.activity_id,
                                     comment=comment,
                                     private=private)
        if current_user.is_administrator():
            activity_entry.creator_role = 'admin'
        else:
            activity_entry.creator_role = 'parent'
        student.activity.append(activity_entry)
        activity.student.append(activity_entry)
        db.session.commit()
        return redirect(url_for('main.students', student_id=student.student_id))
    form.activity_date.data = datetime.utcnow().date()
    form.activity_time.data = datetime.utcnow().time()
    if activity is None:
        abort(404)
    if form is None:
        abort(404)
    else:
        return render_template('activity_detail.html', activity=activity, student=student, form=form)


# @main.route("/activity-detail", methods=['GET', 'POST'])
# @login_required
# def activity_detail():
#     chosen_activity_id = session.get('chosen_activity_id', None)
#     activity = Activity.query.filter_by(activity_id=chosen_activity_id).first()
#     student_ref = session.get('student_ref', None)
#     student = Student.query.filter_by(student_id=student_ref).first()
#     form = None
#     form2 = None
#     id_inc = 1001
#     # ACTIVITY CREATION
#     # ABSENT
#     if activity.activity_name == 'Absent':
#         form = AbsentActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc,
#                                          timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # AUDIO
#     if activity.activity_name == 'Audio':
#         form = AudioActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             comment = form.comment.data
#             private = form.privacy.data
#             file = audio.save(form.upload.data)
#             file_url = audio.url(file)
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=datetime.combine(activity_date, activity_time),
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          filename=file_url,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # CHECK-IN
#     if activity.activity_name == 'Check-in':
#         form = CheckinActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # CHECK-OUT
#     if activity.activity_name == 'Check-out':
#         form = CheckoutActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # FOOD
#     if activity.activity_name == 'Food':
#         form = FoodActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # INCIDENT
#     if activity.activity_name == 'Incident':
#         form = IncidentActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # KUDOS
#     if activity.activity_name == 'Kudos':
#         form = KudosActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # LEARNING
#     if activity.activity_name == 'Learning':
#         form = LearningActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # MEDICATION
#     if activity.activity_name == 'Medication':
#         form = MedicationActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # NAP
#     if activity.activity_name == 'Nap':
#         form = NapActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # NOTE
#     if activity.activity_name == 'Note':
#         form = NoteActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # PHOTO
#     if activity.activity_name == 'Photo':
#         form = PhotoActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             comment = form.comment.data
#             private = form.privacy.data
#             file = photos.save(form.upload.data)
#             file_url = photos.url(file)
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=datetime.combine(activity_date, activity_time),
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          filename=file_url,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # POTTY
#     if activity.activity_name == 'Potty':
#         form = PottyActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # REMINDER
#     if activity.activity_name == 'Reminder':
#         form = ReminderActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             activity_datetime = datetime.combine(activity_date, activity_time)
#             comment = form.comment.data
#             private = form.privacy.data
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=activity_datetime,
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     # VIDEO
#     if activity.activity_name == 'Video':
#         form = VideoActivityForm()
#         if form.validate_on_submit():
#             activity_date = form.activity_date.data
#             activity_time = form.activity_time.data
#             comment = form.comment.data
#             private = form.privacy.data
#             file = videos.save(form.upload.data)
#             file_url = videos.url(file)
#             if ActivityLog.query.filter_by(students=student).all():
#                 last = ActivityLog.query.filter_by(students=student).order_by(ActivityLog.timestamp.desc()).first()
#                 id_inc = last.id + 1
#             activity_entry = ActivityLog(id=id_inc, timestamp=datetime.combine(activity_date, activity_time),
#                                          student_id=student.student_id,
#                                          activity_id=activity.activity_id,
#                                          comment=comment,
#                                          filename=file_url,
#                                          private=private)
#             if current_user.is_administrator():
#                 activity_entry.creator_role = 'admin'
#             else:
#                 activity_entry.creator_role = 'parent'
#             student.activity.append(activity_entry)
#             activity.student.append(activity_entry)
#             db.session.commit()
#             return redirect(url_for('main.student', student_id=student.student_id))
#         form.activity_date.data = datetime.utcnow().date()
#         form.activity_time.data = datetime.utcnow().time()
#     if activity is None:
#         abort(404)
#     if form is None:
#         abort(404)
#     else:
#         return render_template('activity_detail.html', activity=activity, student=student.first_name,
#                                form=form, form2=form2)


@main.route("/edit-activity-detail/<id>", methods=['GET', 'POST'])
@login_required
def edit_activity_detail(id):
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    activity = ActivityLog.query.filter_by(id=id, student_id=student.student_id).first()
    timestamp = activity.timestamp
    # ACTIVITY EDIT
    # ABSENT
    form = None
    if activity.activities.activity_name == 'Absent':
        form = AbsentActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # AUDIO
    if activity.activities.activity_name == 'Audio':
        form = AudioActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            file = audio.save(form.upload.data)
            file_url = audio.url(file)
            activity.filename = file_url
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # CHECK-IN
    if activity.activities.activity_name == 'Check-in':
        form = CheckinActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # CHECK-OUT
    if activity.activities.activity_name == 'Check-out':
        form = CheckoutActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # FOOD
    if activity.activities.activity_name == 'Food':
        form = FoodActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # INCIDENT
    if activity.activities.activity_name == 'Incident':
        form = IncidentActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # KUDOS
    if activity.activities.activity_name == 'Kudos':
        form = KudosActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # LEARNING
    if activity.activities.activity_name == 'Learning':
        form = LearningActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # MEDICATION
    if activity.activities.activity_name == 'Medication':
        form = MedicationActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # NAP
    if activity.activities.activity_name == 'Nap':
        form = NapActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # NOTE
    if activity.activities.activity_name == 'Note':
        form = NoteActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # PHOTO
    if activity.activities.activity_name == 'Photo':
        form = PhotoActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            file = photos.save(form.upload.data)
            file_url = photos.url(file)
            activity.filename = file_url
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # POTTY
    if activity.activities.activity_name == 'Potty':
        form = PottyActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # REMINDER
    if activity.activities.activity_name == 'Reminder':
        form = ReminderActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    # VIDEO
    if activity.activities.activity_name == 'Video':
        form = VideoActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            activity.timestamp = activity_datetime
            activity.comment = comment
            activity.private = private
            file = videos.save(form.upload.data)
            file_url = videos.url(file)
            activity.filename = file_url
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('main.student', student_id=student.student_id))
        form.activity_date.data = activity.timestamp.date()
        form.activity_time.data = activity.timestamp.time()
        form.comment.data = activity.comment
    return render_template('edit_activity_detail.html',
                           timestamp=timestamp,
                           activity=activity,
                           student=student.first_name,
                           form=form
                           )


@main.route("/delete-activity/<id>", methods=['GET', 'POST'])
@login_required
def delete_activity(id):
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    activity = ActivityLog.query.filter_by(id=id, student_id=student.student_id).first()
    db.session.delete(activity)
    db.session.commit()
    flash('Activity successfully deleted')
    return redirect(url_for('main.student', student_id=student.student_id))


@main.route("/create-student", methods=['GET', 'POST'])
@login_required
@admin_required
def create_student():
    form = StudentForm()
    form.gender.choices = [(gender.gender_id, gender.gender_name) for gender in Gender.query.all()]
    form.gender.choices.insert(0, ('0', '-- Choose gender --'))
    form.status.choices = [(status.status_id, status.status_name)
                           for status in Status.query.order_by(Status.status_name).all()]
    form.status.choices.insert(0, ('0', '-- Choose status --'))
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        gender = Gender.query.get(form.gender.data)
        date_of_birth = form.date_of_birth.data
        notes = form.notes.data
        student = Student(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            notes=notes)
        student.school = current_user.school
        new_status = Status.query.get(form.status.data)
        status_entry = StudentStatus(student_id=student.student_id, status_id=new_status.status_id)
        student.status.append(status_entry)
        new_status.student.append(status_entry)
        db.session.add_all([student, status_entry])
        db.session.commit()
        return redirect(request.args.get('next') or url_for('main.students'))
    return render_template('create_student.html', form=form)


@main.route("/edit-student", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student():
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    form = StudentForm()
    form.gender.choices = [(gender.gender_id, gender.gender_name) for gender in Gender.query.all()]
    form.gender.choices.insert(0, ('0', '-- Choose gender --'))
    form.status.choices = [(status.status_id, status.status_name)
                           for status in Status.query.order_by(Status.status_name).all()]
    form.status.choices.insert(0, ('0', '-- Choose status --'))
    if form.validate_on_submit():
        student.first_name = form.first_name.data
        student.last_name = form.last_name.data
        student.gender = Gender.query.get(form.gender.data)
        student.date_of_birth = form.date_of_birth.data
        student.notes = form.notes.data
        new_status = Status.query.get(form.status.data)
        status_entry = StudentStatus(student_id=student.student_id, status_id=new_status.status_id)
        student.status.append(status_entry)
        new_status.student.append(status_entry)
        db.session.add_all([student, status_entry])
        db.session.commit()
        return redirect(url_for('main.student', student_id=student.student_id))
    form.first_name.data = student.first_name
    form.last_name.data = student.last_name
    form.gender.data = student.gender_id
    form.date_of_birth.data = student.date_of_birth
    student_status = StudentStatus.query.filter_by(
        students=student).order_by(StudentStatus.timestamp.desc()).first()
    if student_status:
        form.status.data = student_status.status_id
    form.notes.data = student.notes
    return render_template('edit_student.html', form=form)


@main.route("/delete-student", methods=['GET', 'POST'])
@login_required
@admin_required
def delete_student():
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    db.session.delete(student)
    db.session.commit()
    flash('Student successfully deleted')
    return redirect(url_for('main.students'))


@main.route("/student-avatar", methods=['GET', 'POST'])
@login_required
@admin_required
def student_avatar():
    form = AvatarForm()
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    if form.validate_on_submit():
        avatar = photos.save(form.avatar.data)
        student.avatar = avatar
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('main.student', student_id=student.student_id))
    return render_template('avatar.html', form=form)


@main.route("/parents")
@login_required
@admin_required
def parents():
    parents = Parent.query.filter_by(school=current_user.school).all()
    return render_template('parents.html', parents=parents)


@main.route("/parent/<parent_id>", methods=['GET', 'POST'])
@login_required
@admin_required
def parent(parent_id):
    parent = Parent.query.filter_by(parent_id=parent_id).first()
    form1 = StudentParentForm()
    form2 = ContactNumberForm()
    # form3 = EditContactNumberForm()
    form1.student.choices = [(student.student_id,
                             student.last_name + ', ' + student.first_name
                             ) for student in Student.query.filter_by(
        school=current_user.school).all()]
    form1.student.choices.insert(0, ('0', '-- Choose a student --'))
    session['parent_ref'] = parent.parent_id
    # if form1.validate_on_submit():
    if form1.submit.data and form1.validate():
        parent.student.append(Student.query.get(form1.student.data))
        db.session.add(parent)
        db.session.commit()
        return redirect(url_for('.parent', parent_id=parent.parent_id))
    if form2.submit2.data and form2.validate():
        number = form2.contact_number.data
        primary = form2.primary_number.data
        c = Contact(contact=number, primary_number=primary)
        parent.contact.append(c)
        db.session.add_all([parent, c])
        db.session.commit()
        return redirect(url_for('.parent', parent_id=parent.parent_id))
    if parent is None:
        abort(404)
    if parent.school == current_user.school:
        return render_template('parent.html', parent=parent, form1=form1, form2=form2)
    else:
        abort(404)


@main.route("/delete-parent", methods=['GET', 'POST'])
@login_required
@admin_required
def delete_parent():
    parent_ref = session.get('parent_ref', None)
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    user_ref = parent.user.id
    user = User.query.filter_by(id=user_ref).first()
    db.session.delete(parent)
    db.session.delete(user)
    db.session.commit()
    flash('Parent successfully deleted')
    return redirect(url_for('main.parents'))


# ALLOWS PARENTS TO ADD CONTACT NUMBERS FROM THE USER PAGE / THEIR PROFILE PAGE
@main.route("/add-contact", methods=['GET', 'POST'])
@login_required
def add_contact():
    parent = Parent.query.filter_by(parent_id=current_user.parent.parent_id).first()
    form = ContactNumberForm()
    if form.validate_on_submit():
        number = form.contact_number.data
        primary = form.primary_number.data
        c = Contact(contact=number, primary_number=primary)
        parent.contact.append(c)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('.user', username=current_user.username))
    return render_template('add_contact.html', form=form, parent=parent)


@main.route("/edit-contact/<contact_id>", methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    parent_ref = session.get('parent_ref', None)
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    c = Contact.query.filter_by(contact_id=contact_id).first()
    form3 = EditContactNumberForm()
    if form3.validate_on_submit():
        c.contact = form3.contact_number.data
        c.primary_number = form3.primary_number.data
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('.parent', parent_id=parent.parent_id))
    form3.contact_number.data = c.contact
    form3.primary_number.data = c.primary_number
    return render_template('edit_contact.html', parent=parent, form3=form3)


@main.route("/edit-my-contact/<contact_id>", methods=['GET', 'POST'])
@login_required
def edit_my_contact(contact_id):
    parent = Parent.query.filter_by(parent_id=current_user.parent.parent_id).first()
    c = Contact.query.filter_by(contact_id=contact_id).first()
    form3 = EditContactNumberForm()
    if form3.validate_on_submit():
        c.contact = form3.contact_number.data
        c.primary_number = form3.primary_number.data
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('.user', username=current_user.username))
    form3.contact_number.data = c.contact
    form3.primary_number.data = c.primary_number
    return render_template('edit_contact.html', parent=parent, form3=form3)


@main.route("/delete-contact/<contact_id>", methods=['GET', 'POST'])
@login_required
def delete_contact(contact_id):
    parent_ref = session.get('parent_ref', None)
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    c = Contact.query.filter_by(contact_id=contact_id).first()
    db.session.delete(c)
    db.session.commit()
    flash('Contact number successfully deleted')
    return redirect(url_for('.parent', parent_id=parent.parent_id))


@main.route("/delete-my-contact/<contact_id>", methods=['GET', 'POST'])
@login_required
def delete_my_contact(contact_id):
    # parent = Parent.query.filter_by(parent_id=current_user.parent.parent_id).first()
    c = Contact.query.filter_by(contact_id=contact_id).first()
    db.session.delete(c)
    db.session.commit()
    flash('Contact number successfully deleted')
    return redirect(url_for('.user', username=current_user.username))


@main.route("/delete-student-room", methods=['GET', 'POST'])
@login_required
def delete_student_room():
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    student.room = None
    db.session.add(student)
    db.session.commit()
    flash('Student successfully removed from room')
    return redirect(url_for('main.student', student_id=student.student_id))


# REMOVES A PARENT FROM A STUDENT VIA THE STUDENT'S PAGE
@main.route("/delete-student-parent/<parent_id>", methods=['GET', 'POST'])
@login_required
def delete_student_parent(parent_id):
    student_ref = session.get('student_ref', None)
    student = Student.query.filter_by(student_id=student_ref).first()
    parent = Parent.query.filter_by(parent_id=parent_id).first()
    sp = StudentParent.query.filter_by(student_id=student.student_id, parent_id=parent.parent_id).first()
    db.session.delete(sp)
    db.session.commit()
    flash('Parent successfully removed from student')
    return redirect(url_for('main.student', student_id=student.student_id))


# REMOVES A STUDENT FROM A PARENT VIA THE PARENT'S PAGE
@main.route("/delete-parent-student/<student_id>", methods=['GET', 'POST'])
@login_required
def delete_parent_student(student_id):
    parent_ref = session.get('parent_ref', None)
    student = Student.query.filter_by(student_id=student_id).first()
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    sp = StudentParent.query.filter_by(student_id=student.student_id, parent_id=parent.parent_id).first()
    db.session.delete(sp)
    db.session.commit()
    flash('Student successfully removed from parent')
    return redirect(url_for('main.parent', parent_id=parent.parent_id))


@main.route("/parent-address", methods=['GET', 'POST'])
@login_required
def parent_address():
    parent_ref = current_user.parent.parent_id
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    form = AddressForm()
    if form.validate_on_submit():
        address_line1 = form.address_line1.data
        address_line2 = form.address_line2.data
        address_city = form.address_city.data
        address_region = form.address_region.data
        address_post_code = form.address_post_code.data
        address_country = form.address_country.data
        address = Address(address_line1=address_line1, address_line2=address_line2, address_city=address_city,
                          address_region=address_region, address_post_code=address_post_code,
                          address_country=address_country)
        parent.address = address
        db.session.add_all([parent, address])
        return redirect(url_for('main.user', username=current_user.username))
    if parent.address:
        form.address_line1.data = parent.address.address_line1
        form.address_line2.data = parent.address.address_line2
        form.address_city.data = parent.address.address_city
        form.address_region.data = parent.address.address_region
        form.address_post_code.data = parent.address.address_post_code
        form.address_country.data = parent.address.address_country
    return render_template('parent_address.html', form=form, parent=parent)


@main.route("/parent-address-admin", methods=['GET', 'POST'])
@login_required
@admin_required
def parent_address_admin():
    parent_ref = session.get('parent_ref', None)
    parent = Parent.query.filter_by(parent_id=parent_ref).first()
    form = AddressForm()
    if form.validate_on_submit():
        address_line1 = form.address_line1.data
        address_line2 = form.address_line2.data
        address_city = form.address_city.data
        address_region = form.address_region.data
        address_post_code = form.address_post_code.data
        address_country = form.address_country.data
        address = Address(address_line1=address_line1, address_line2=address_line2, address_city=address_city,
                          address_region=address_region, address_post_code=address_post_code,
                          address_country=address_country)
        parent.address = address
        db.session.add_all([parent, address])
        return redirect(url_for('.parent', parent_id=parent.parent_id))
    if parent.address:
        form.address_line1.data = parent.address.address_line1
        form.address_line2.data = parent.address.address_line2
        form.address_city.data = parent.address.address_city
        form.address_region.data = parent.address.address_region
        form.address_post_code.data = parent.address.address_post_code
        form.address_country.data = parent.address.address_country
    return render_template('parent_address_admin.html', form=form, parent=parent)


@main.route("/school-address", methods=['GET', 'POST'])
@login_required
@admin_required
def school_address():
    school = current_user.school
    user = current_user
    form = AddressForm()
    if form.validate_on_submit():
        school.address.address_line1 = form.address_line1.data
        school.address.address_line2 = form.address_line2.data
        school.address.address_city = form.address_city.data
        school.address.address_region = form.address_region.data
        school.address.address_post_code = form.address_post_code.data
        school.address.address_country = form.address_country.data
        db.session.add_all([school])
        return redirect(url_for('.user', username=user.username))
    if school.address:
        form.address_line1.data = school.address.address_line1
        form.address_line2.data = school.address.address_line2
        form.address_city.data = school.address.address_city
        form.address_region.data = school.address.address_region
        form.address_post_code.data = school.address.address_post_code
        form.address_country.data = school.address.address_country
    return render_template('school_address.html', form=form, school=school)


@main.route("/edit-school-name", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_school_name():
    school = current_user.school
    user = current_user
    form = SchoolNameForm()
    if form.validate_on_submit():
        school.school_name = form.school_name.data
        db.session.add_all([school])
        return redirect(url_for('.user', username=user.username))
    form.school_name.data = school.school_name
    return render_template('edit_school_name.html', form=form, school=school)


@main.route("/user/<username>", methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    if user.school_id == current_user.school_id and user.role == current_user.role and current_user.is_administrator() \
            or user == current_user:
        return render_template('user.html'
                               , user=user)
    else:
        abort(404)


@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template('change_password.html', form=form)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    form = EditProfileForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        db.session.add(user)
        flash('Your profile has been successfully updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    # form.role.choices = [(role.role_id, role.role_name) for role in Role.query.order_by(Role.role_name).all()]
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        # user.role = Role.query.get(form.role.data)
        db.session.add(user)
        flash('This profile has been successfully updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    # form.role.data = user.role_id
    if current_user.school == user.school:
        return render_template('edit_profile.html', form=form, user=user)
    else:
        abort(404)


@main.route('/upload-old', methods=['GET', 'POST'])
@login_required
def upload_old():
    if request.method == 'POST' and 'photo' in request.files:
        try:
            filename = photos.save(request.files['photo'])
            flash('{} uploaded successfully'.format(filename))
            return redirect(url_for('.upload_old'))
        except:
            flash("Upload unsuccessful. Please ensure you're uploading an image")
            return redirect(url_for('.upload_old'))
    return render_template('uploads_test_old.html')


@main.route('/group-activity', methods=['GET', 'POST'])
@login_required
@admin_required
def group_activity():
    form = GroupActivityForm()
    form.activity.choices = [(activity.activity_id, activity.activity_name) for activity
                                      in Activity.query.order_by(Activity.activity_name).all()]
    form.activity.choices.insert(0, ('0', '-- Choose an activity --'))
    form.students.choices = [(student.student_id,
                              student.last_name + ', ' + student.first_name
                              ) for student in Student.query.filter_by(
        school=current_user.school).all()]
    chosen_activity = None
    students = None
    number_of_students = 0
    if form.validate_on_submit():
        students = form.students.data
        chosen_activity = Activity.query.get(form.activity.data)
        number_of_students = len(students)
        session['activity_ref'] = chosen_activity.activity_id
        session['student_group_ref'] = students
        session['group_size_ref'] = number_of_students
        return redirect(url_for('.group_activity_detail'))
    return render_template('group_activity.html'
                           , form=form
                           , chosen_activity=chosen_activity
                           , students=students
                           , number_of_students=number_of_students)


@main.route('/group-activity-detail', methods=['GET', 'POST'])
@login_required
@admin_required
def group_activity_detail():
    activity_ref = session.get('activity_ref', None)
    activity = Activity.query.filter_by(activity_id=activity_ref).first()
    student_group_ref = session.get('student_group_ref', None)
    group_size_ref = session.get('group_size_ref', None)
    student = []
    form = None
    for id in student_group_ref:
        student.append(Student.query.filter_by(student_id=id).first())
    # GROUP ACTIVITY CREATION
    # ABSENT
    if activity.activity_name == 'Absent':
        form = AbsentActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # AUDIO
    if activity.activity_name == 'Audio':
        form = AudioActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            file = photos.save(form.upload.data)
            file_url = audio.url(file)
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             filename=file_url,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # CHECK-IN
    if activity.activity_name == 'Check-in':
        form = CheckinActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # CHECK-OUT
    if activity.activity_name == 'Check-out':
        form = CheckoutActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # FOOD
    if activity.activity_name == 'Food':
        form = FoodActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # INCIDENT
    if activity.activity_name == 'Incident':
        form = IncidentActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # KUDOS
    if activity.activity_name == 'Kudos':
        form = KudosActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # LEARNING
    if activity.activity_name == 'Learning':
        form = LearningActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # MEDICATION
    if activity.activity_name == 'Medication':
        form = MedicationActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # NAP
    if activity.activity_name == 'Nap':
        form = NapActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # NOTE
    if activity.activity_name == 'Note':
        form = NoteActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # PHOTO
    if activity.activity_name == 'Photo':
        form = PhotoActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            file = photos.save(form.upload.data)
            file_url = photos.url(file)
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             filename=file_url,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # POTTY
    if activity.activity_name == 'Potty':
        form = PottyActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # REMINDER
    if activity.activity_name == 'Reminder':
        form = ReminderActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    # VIDEO
    if activity.activity_name == 'Video':
        form = VideoActivityForm()
        if form.validate_on_submit():
            activity_date = form.activity_date.data
            activity_time = form.activity_time.data
            activity_datetime = datetime.combine(activity_date, activity_time)
            comment = form.comment.data
            private = form.privacy.data
            file = photos.save(form.upload.data)
            file_url = photos.url(file)
            for s in student:
                id_inc = 1001
                if ActivityLog.query.filter_by(students=s).all():
                    last = ActivityLog.query.filter_by(
                        students=s).order_by(ActivityLog.timestamp.desc()).first()
                    id_inc = last.id + 1
                activity_entry = ActivityLog(id=id_inc,
                                             timestamp=activity_datetime,
                                             student_id=s.student_id,
                                             activity_id=activity.activity_id,
                                             comment=comment,
                                             filename=file_url,
                                             private=private)
                activity_entry.creator_role = 'admin'
                s.activity.append(activity_entry)
                activity.student.append(activity_entry)
                db.session.commit()
            flash('Group activity successfully added for {} students'.format(group_size_ref))
            return redirect(url_for('main.students'))
        form.activity_date.data = datetime.utcnow().date()
        form.activity_time.data = datetime.utcnow().time()
    return render_template('group_activity_detail.html'
                           , activity=activity
                           , student=student
                           , student_group_ref=student_group_ref
                           , group_size_ref=group_size_ref
                           , form=form)


# @main.route('/uploads-test', methods=['GET', 'POST'])
# @login_required
# def uploads_test():
#     return render_template('uploads_test.html')
#
#
# # Listen for POST requests to yourdomain.com/submit_form/
# @main.route('/submit-form/', methods=['POST'])
# @login_required
# def submit_form():
#     username = request.form["username"]
#     full_name = request.form["full-name"]
#     avatar_url = request.form["avatar-url"]
#     session['username_ref'] = username
#     session['full_name_ref'] = full_name
#     session['avatar_ref'] = avatar_url
#
#     # Provide some procedure for storing the new details
#     # update_account(username, full_name, avatar_url)
#
#     return redirect(url_for('main.uploads_test_output'))
#
#
# @main.route('/uploads_test_output', methods=['GET', 'POST'])
# @login_required
# def uploads_test_output():
#     username = session.get('username_ref', None)
#     full_name = session.get('full_name_ref', None)
#     avatar_url = session.get('avatar_ref', None)
#     return render_template('uploads_test_output.html'
#                            , username=username
#                            , full_name=full_name
#                            , avatar_url=avatar_url)
#
#
# @main.route('/sign_s3/')
# def sign_s3():
#     S3_BUCKET = os.environ.get('S3_BUCKET')
#
#     file_name = request.args.get('file_name')
#     file_type = request.args.get('file_type')
#
#     s3 = boto3.client('s3')
#
#     presigned_post = s3.generate_presigned_post(
#         Bucket=S3_BUCKET,
#         Key=file_name,
#         Fields={"acl": "public-read", "Content-Type": file_type},
#         Conditions=[
#           {"acl": "public-read"},
#           {"Content-Type": file_type}
#         ],
#         ExpiresIn=3600
#         )
#
#     return json.dumps({'data': presigned_post, 'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)})


@main.route('/uploads-test', methods=['GET', 'POST'])
@login_required
def uploads_test():
    s3 = boto3.resource('s3')
    s3.Bucket('psa-one').put_object(key='my_image.png', body=request.files['file_input'])
    return '<h1>File saved to S3</h1>'
