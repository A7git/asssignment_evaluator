"""Evaluation results model."""
import json
from datetime import datetime, timezone
from ..extensions import db


class Evaluation(db.Model):
    """Stores evaluation results for a submission."""
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'),
                              nullable=False, unique=True)

    # Score components (0-100 scale)
    correctness_score = db.Column(db.Float, default=0.0)
    style_score = db.Column(db.Float, default=0.0)
    similarity_score = db.Column(db.Float, default=0.0)  # How similar to reference
    clarity_score = db.Column(db.Float, default=0.0)
    completeness_score = db.Column(db.Float, default=0.0)
    plagiarism_score = db.Column(db.Float, default=100.0)  # 100 = fully original
    final_score = db.Column(db.Float, default=0.0)

    # Detailed feedback
    feedback_json = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)

    # Plagiarism details
    plagiarism_details_json = db.Column(db.Text, nullable=True)

    # Code execution results
    test_results_json = db.Column(db.Text, nullable=True)

    evaluated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def feedback(self):
        if self.feedback_json:
            try:
                return json.loads(self.feedback_json)
            except json.JSONDecodeError:
                return {}
        return {}

    @feedback.setter
    def feedback(self, value):
        self.feedback_json = json.dumps(value)

    @property
    def plagiarism_details(self):
        if self.plagiarism_details_json:
            try:
                return json.loads(self.plagiarism_details_json)
            except json.JSONDecodeError:
                return {}
        return {}

    @plagiarism_details.setter
    def plagiarism_details(self, value):
        self.plagiarism_details_json = json.dumps(value)

    @property
    def test_results(self):
        if self.test_results_json:
            try:
                return json.loads(self.test_results_json)
            except json.JSONDecodeError:
                return []
        return []

    @test_results.setter
    def test_results(self, value):
        self.test_results_json = json.dumps(value)

    @property
    def grade_letter(self):
        """Convert final score to letter grade."""
        score = self.final_score
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

    @property
    def grade_color(self):
        """Color for the grade display."""
        score = self.final_score
        if score >= 80:
            return '#00d4aa'
        elif score >= 60:
            return '#667eea'
        elif score >= 40:
            return '#ffa726'
        else:
            return '#ff5252'

    def __repr__(self):
        return f'<Evaluation submission={self.submission_id} score={self.final_score}>'
