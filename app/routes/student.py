"""Student portal routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models.submission import Submission
from ..models.assignment import Assignment
from ..extensions import db

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.before_request
@login_required
def check_student():
    if current_user.role != 'student':
        flash('Access restricted to students.', 'danger')
        return redirect(url_for('dashboard.index'))


@student_bp.route('/dashboard')
def dashboard():
    """Student dashboard showing active assignments and recent submissions."""
    # Get all assignments
    assignments = Assignment.query.order_by(Assignment.due_date.desc()).all()
    
    # Get user's submissions
    submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    
    return render_template('student/dashboard.html', 
                           assignments=assignments, 
                           submissions=submissions)


@student_bp.route('/report/<int:submission_id>')
def report(submission_id):
    """View submission report if released by faculty."""
    submission = Submission.query.get_or_404(submission_id)
    
    # Security check: must be owner
    if submission.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    if not submission.is_released:
        flash('This report has not been released by the instructor yet.', 'info')
        return redirect(url_for('student.dashboard'))
    
    if not submission.evaluation:
        flash('Evaluation in progress.', 'info')
        return redirect(url_for('student.dashboard'))
        
    return render_template('student/report.html', submission=submission)
