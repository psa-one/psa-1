"""initial migration

Revision ID: 02d794fd667e
Revises: 
Create Date: 2018-05-02 22:31:22.647000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02d794fd667e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activities',
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('activity_name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('activity_id'),
    sa.UniqueConstraint('activity_name')
    )
    op.create_table('addresses',
    sa.Column('address_id', sa.Integer(), nullable=False),
    sa.Column('address_line1', sa.String(length=64), nullable=True),
    sa.Column('address_line2', sa.String(length=64), nullable=True),
    sa.Column('address_city', sa.String(length=64), nullable=True),
    sa.Column('address_region', sa.String(length=64), nullable=True),
    sa.Column('address_post_code', sa.String(length=64), nullable=True),
    sa.Column('address_country', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('address_id')
    )
    op.create_table('contacts',
    sa.Column('contact_id', sa.Integer(), nullable=False),
    sa.Column('contact', sa.String(length=64), nullable=True),
    sa.Column('primary_number', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('contact_id')
    )
    op.create_table('gender',
    sa.Column('gender_id', sa.Integer(), nullable=False),
    sa.Column('gender_name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('gender_id'),
    sa.UniqueConstraint('gender_name')
    )
    op.create_table('roles',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('role_name', sa.String(length=64), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('role_id'),
    sa.UniqueConstraint('role_name')
    )
    op.create_index(op.f('ix_roles_default'), 'roles', ['default'], unique=False)
    op.create_table('status',
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('status_name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('status_id'),
    sa.UniqueConstraint('status_name')
    )
    op.create_table('title',
    sa.Column('title_id', sa.Integer(), nullable=False),
    sa.Column('title_name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('title_id'),
    sa.UniqueConstraint('title_name')
    )
    op.create_table('schools',
    sa.Column('school_id', sa.Integer(), nullable=False),
    sa.Column('school_name', sa.String(length=64), nullable=True),
    sa.Column('address_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['address_id'], ['addresses.address_id'], ),
    sa.PrimaryKeyConstraint('school_id')
    )
    op.create_index(op.f('ix_schools_school_name'), 'schools', ['school_name'], unique=False)
    op.create_table('rooms',
    sa.Column('room_id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('room_name', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.school_id'], ),
    sa.PrimaryKeyConstraint('room_id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('member_since', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ),
    sa.ForeignKeyConstraint(['school_id'], ['schools.school_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('parents',
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.Column('title_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('address_id', sa.Integer(), nullable=True),
    sa.Column('first_name', sa.String(length=64), nullable=True),
    sa.Column('last_name', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['address_id'], ['addresses.address_id'], ),
    sa.ForeignKeyConstraint(['school_id'], ['schools.school_id'], ),
    sa.ForeignKeyConstraint(['title_id'], ['title.title_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('parent_id')
    )
    op.create_table('students',
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('gender_id', sa.Integer(), nullable=True),
    sa.Column('avatar', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(length=64), nullable=True),
    sa.Column('last_name', sa.String(length=64), nullable=True),
    sa.Column('date_of_birth', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('room_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gender_id'], ['gender.gender_id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.room_id'], ),
    sa.ForeignKeyConstraint(['school_id'], ['schools.school_id'], ),
    sa.PrimaryKeyConstraint('student_id')
    )
    op.create_index(op.f('ix_students_date_of_birth'), 'students', ['date_of_birth'], unique=False)
    op.create_table('activity_log',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('creator_role', sa.String(), nullable=True),
    sa.Column('private', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['activities.activity_id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ),
    sa.PrimaryKeyConstraint('timestamp', 'student_id', 'activity_id')
    )
    op.create_index(op.f('ix_activity_log_id'), 'activity_log', ['id'], unique=False)
    op.create_index(op.f('ix_activity_log_timestamp'), 'activity_log', ['timestamp'], unique=False)
    op.create_table('parent_contact',
    sa.Column('phone_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['parents.parent_id'], ),
    sa.ForeignKeyConstraint(['phone_id'], ['contacts.contact_id'], ),
    sa.PrimaryKeyConstraint('phone_id', 'parent_id')
    )
    op.create_table('student_parent',
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['parents.parent_id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ),
    sa.PrimaryKeyConstraint('student_id', 'parent_id')
    )
    op.create_table('student_status',
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['status_id'], ['status.status_id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ),
    sa.PrimaryKeyConstraint('timestamp', 'student_id', 'status_id')
    )
    op.create_index(op.f('ix_student_status_timestamp'), 'student_status', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_student_status_timestamp'), table_name='student_status')
    op.drop_table('student_status')
    op.drop_table('student_parent')
    op.drop_table('parent_contact')
    op.drop_index(op.f('ix_activity_log_timestamp'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_id'), table_name='activity_log')
    op.drop_table('activity_log')
    op.drop_index(op.f('ix_students_date_of_birth'), table_name='students')
    op.drop_table('students')
    op.drop_table('parents')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('rooms')
    op.drop_index(op.f('ix_schools_school_name'), table_name='schools')
    op.drop_table('schools')
    op.drop_table('title')
    op.drop_table('status')
    op.drop_index(op.f('ix_roles_default'), table_name='roles')
    op.drop_table('roles')
    op.drop_table('gender')
    op.drop_table('contacts')
    op.drop_table('addresses')
    op.drop_table('activities')
    # ### end Alembic commands ###