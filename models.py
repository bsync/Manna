from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import flask_user

class MannaDB(SQLAlchemy):
    def init_app(self, app):
        super().init_app(app)
        # Create default user with 'Admin' and 'EndUser' roles
        with app.app_context():
            self.create_all()
            if not User.query.filter(User.email == 'james.horine@gmail.com').first():
                user = User(
                    username='admin',
                    email='james.horine@gmail.com',
                    email_confirmed_at=datetime.utcnow(),
                )
                user.roles.append(Role(name='Admin'))
                user.roles.append(Role(name='EndUser'))
                self.session.add(user)
                self.session.commit()

mdb = db = MannaDB()

class User(db.Model, flask_user.UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')
    @property
    def is_active(self):
        return self.active

    @property
    def role_names(self):
        return ", ".join([r.name for r in self.roles])


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))
