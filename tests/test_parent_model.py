import unittest
from app.models import User, Role, Permission, AnonymousUser, \
    ActivityLog, Activity, StudentStatus, Status, Room, Student, Parent, StudentParent


class ParentModelTestCase(unittest.TestCase):
    def test_parent_student_creation(self):
        s1 = Student(first_name="billy")
        p1 = Parent(first_name="mary_mum")
        p2 = Parent(first_name="bob_dad")
        s1.parent.append(p1)
        s1.parent.append(p2)
        self.assertTrue(len(s1.parent) == 2)

    def test_parent_user_creation(self):
        u = User(username='azille78')
        p = Parent(first_name='bella')
        u.parent = p
        self.assertTrue(p.user.username == 'azille78')

