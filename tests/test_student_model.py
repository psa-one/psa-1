import unittest
from app.models import User, Role, Permission, AnonymousUser, \
    ActivityLog, Activity, StudentStatus, Status, Room, Student, Parent, StudentParent


class StudentModelTestCase(unittest.TestCase):
    def test_activity_logging(self):
        s = Student(first_name='billy')
        act1 = Activity(activity_name='nap')
        act_entry1 = ActivityLog(student_id=s.student_id, activity_id=act1.activity_id)
        s.activity.append(act_entry1)
        act1.student.append(act_entry1)
        act_entry2 = ActivityLog(student_id=s.student_id, activity_id=act1.activity_id)
        s.activity.append(act_entry2)
        act1.student.append(act_entry2)
        self.assertTrue(len(s.activity) == 2)

    def test_status_logging(self):
        s = Student(first_name='billy')
        stat1 = Status(status_name='Lead')
        stat2 = Status(status_name='Active')
        stat_entry1 = StudentStatus(student_id=s.student_id, status_id=stat1.status_id)
        s.status.append(stat_entry1)
        stat1.student.append(stat_entry1)
        stat_entry2 = StudentStatus(student_id=s.student_id, status_id=stat2.status_id)
        s.status.append(stat_entry2)
        stat2.student.append(stat_entry2)
        stat_entry3 = StudentStatus(student_id=s.student_id, status_id=stat1.status_id)
        s.status.append(stat_entry3)
        stat1.student.append(stat_entry3)
        self.assertTrue(len(s.status) == 3)

    def test_room_allocation(self):
        r1 = Room(room_name="Demo Room 1")
        r2 = Room(room_name="Demo Room 2")
        s1 = Student(first_name="billy")
        s2 = Student(first_name="bella")
        s3 = Student(first_name="mikes")
        s1.room = r1
        s2.room = r1
        s3.room = r2
        self.assertTrue(s1 in r1.students)
        self.assertTrue(s2 in r1.students)
        self.assertTrue(s3 in r2.students)
