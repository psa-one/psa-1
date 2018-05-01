import os
from app import create_app, db
from app.models import Student, Status, StudentStatus, School, Room, Activity, ActivityLog, Parent, StudentParent, \
    Role, User, Contact, ParentContact, Address, Gender, Title
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Student=Student, Status=Status, StudentStatus=StudentStatus, School=School,
                Room=Room, Activity=Activity, ActivityLog=ActivityLog, Parent=Parent, StudentParent=StudentParent,
                Role=Role, User=User, Contact=Contact, ParentContact=ParentContact, Address=Address, Gender=Gender,
                Title=Title
                )


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, Activity, Status, Gender, Title

    # migrate database to latest version
    upgrade()

    Role.insert_roles()
    Activity.insert_activities()
    Status.insert_statuses()
    Gender.insert_genders()
    Title.insert_titles()


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    manager.run()
