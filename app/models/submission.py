"""Student submission model."""
from datetime import datetime, timezone
from ..extensions import db


class Submission(db.Model):
    """A student's submitted assignment."""
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Link to User account
    student_id = db.Column(db.String(50), nullable=False, index=True) # Keep for quick access/legacy
    student_name = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # e.g., 'pdf', 'py', 'java'
    extracted_text = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')  # 'pending', 'evaluating', 'evaluated', 'error'
    is_released = db.Column(db.Boolean, default=False)  # Whether student can see the grade

    # Relationship
    evaluation = db.relationship('Evaluation', backref='submission', uselist=False,
                                 cascade='all, delete-orphan')

    @property
    def is_code(self):
        return self.file_type in ('py', 'java', 'cpp', 'c')

    @property
    def is_document(self):
        return self.file_type in ('pdf', 'docx', 'doc', 'txt')

    @property
    def status_color(self):
        colors = {
            'pending': 'warning',
            'evaluating': 'info',
            'evaluated': 'success',
            'error': 'danger'
        }
        return colors.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Submission {self.student_id} - {self.file_name}>'
