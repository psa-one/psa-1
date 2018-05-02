import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import sys
import click
from app import create_app, db
from app.models import Student, Status, StudentStatus, School, Room, Activity, ActivityLog, Parent, StudentParent, \
    Role, User, Contact, ParentContact, Address, Gender, Title
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand, upgrade


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


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


# if __name__ == "__main__":
#     manager.run()
@app.cli.command()
@click.option('--length', default=25,
              help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
              help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest version
    upgrade()
    Role.insert_roles()
    Activity.insert_activities()
    Status.insert_statuses()
    Gender.insert_genders()
    Title.insert_titles()
