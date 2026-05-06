"""Faculty user model."""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication (Faculty or Student)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'faculty' or 'student'
    student_id = db.Column(db.String(50), unique=True, nullable=True) # Only for students
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = db.relationship('Assignment', backref='faculty', lazy='dynamic')
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_faculty(self):
        return self.role == 'faculty'

    @property
    def is_student(self):
        return self.role == 'student'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
