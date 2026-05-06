"""Assignment and Rubric models."""
import json
from datetime import datetime, timezone
from ..extensions import db


class Assignment(db.Model):
    """Assignment created by faculty."""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assignment_type = db.Column(db.String(20), nullable=False)  # 'coding' or 'descriptive'
    language = db.Column(db.String(20), nullable=True)  # 'python', 'java', 'cpp' or null
    reference_solution = db.Column(db.Text, nullable=True)
    test_cases_json = db.Column(db.Text, nullable=True)  # JSON string
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    rubrics = db.relationship('Rubric', backref='assignment', lazy='select',
                              cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic',
                                  cascade='all, delete-orphan')

    @property
    def test_cases(self):
        """Parse test cases from JSON."""
        if self.test_cases_json:
            try:
                return json.loads(self.test_cases_json)
            except json.JSONDecodeError:
                return []
        return []

    @test_cases.setter
    def test_cases(self, value):
        """Serialize test cases to JSON."""
        self.test_cases_json = json.dumps(value)

    @property
    def submission_count(self):
        return self.submissions.count()

    @property
    def evaluated_count(self):
        return self.submissions.filter_by(status='evaluated').count()

    @property
    def is_coding(self):
        return self.assignment_type == 'coding'

    def __repr__(self):
        return f'<Assignment {self.title}>'


class Rubric(db.Model):
    """Grading rubric criterion for an assignment."""
    __tablename__ = 'rubrics'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    criterion = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Percentage weight (e.g., 40.0)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Rubric {self.criterion}: {self.weight}%>'
