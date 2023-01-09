from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Datastore:

    def __init__(self, app):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///manna.db"
        db.init_app(app)
        with app.app_context():
            db.create_all()

    @property
    def user_count(self):
        return db.session.query(User).count()

    def find_role(self, **kwargs):
        return db.session.query(Role).filter_by(**kwargs).one_or_none()

    def create_role(self, **kwargs):
        db.session.add(Role(**kwargs))
        db.session.commit()

    def find_users(self, **kwargs):
        return db.session.query(User).filter_by(**kwargs)

    def find_user(self, **kwargs):
        return self.find_users(**kwargs).one_or_none()

    def create_user(self, roles=[], **kwargs):
        user = User(**kwargs)
        froles = []
        for r in roles:
            if type(r) == Role:
                froles.append(r)
            else:
                frole = db.session.query(Role).filter_by(name=r).one_or_none()
                if frole:
                    froles.append(frole)
                else:
                    froles.append(Role(name=r))
        user.roles = froles
        db.session.add(user)
        db.session.commit()


class RolesUsers(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    desc = db.Column(db.String(255), nullable=True)
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        'Role', secondary='roles_users',
        backref=db.backref('users', lazy='dynamic'))

    @property
    def is_active(self):
        return self.active

class UserInvitation:
    id = db.Column(db.Integer, primary_key=True)
    # UserInvitation email information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False)
    # save the user of the invitee
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

