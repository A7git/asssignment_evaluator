"""Dashboard routes — faculty analytics."""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from ..extensions import db
from ..models.assignment import Assignment
from ..models.submission import Submission
from ..models.evaluation import Evaluation

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.before_request
@login_required
def check_faculty():
    if current_user.role != 'faculty':
        from flask import flash, redirect, url_for
        flash('Access restricted to faculty members.', 'danger')
        return redirect(url_for('student.dashboard'))


@dashboard_bp.route('/')
@login_required
def index():
    """Faculty analytics dashboard."""
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    total_submissions = Submission.query.count()
    evaluated_count = Submission.query.filter_by(status='evaluated').count()
    pending_count = Submission.query.filter_by(status='pending').count()

    # Average scores
    avg_score = db.session.query(func.avg(Evaluation.final_score)).scalar() or 0
    avg_plagiarism = db.session.query(func.avg(Evaluation.plagiarism_score)).scalar() or 0

    # Recent submissions
    recent = Submission.query.order_by(
        Submission.submitted_at.desc()
    ).limit(10).all()

    return render_template('dashboard/index.html',
                           assignments=assignments,
                           total_submissions=total_submissions,
                           evaluated_count=evaluated_count,
                           pending_count=pending_count,
                           avg_score=round(avg_score, 1),
                           avg_plagiarism=round(avg_plagiarism, 1),
                           recent_submissions=recent)


@dashboard_bp.route('/api/stats')
@login_required
def stats_api():
    """JSON endpoint for dashboard charts."""
    # Score distribution
    evaluations = Evaluation.query.all()
    score_ranges = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for e in evaluations:
        s = e.final_score
        if s <= 20:
            score_ranges['0-20'] += 1
        elif s <= 40:
            score_ranges['21-40'] += 1
        elif s <= 60:
            score_ranges['41-60'] += 1
        elif s <= 80:
            score_ranges['61-80'] += 1
        else:
            score_ranges['81-100'] += 1

    # Per-assignment stats
    assignments = Assignment.query.all()
    assignment_stats = []
    for a in assignments:
        evals = [sub.evaluation for sub in a.submissions.all()
                 if sub.evaluation]
        if evals:
            avg = sum(e.final_score for e in evals) / len(evals)
            assignment_stats.append({
                'title': a.title[:30],
                'avg_score': round(avg, 1),
                'submissions': a.submission_count,
                'evaluated': len(evals)
            })

    # Plagiarism distribution
    plag_ranges = {'90-100': 0, '70-89': 0, '50-69': 0, '0-49': 0}
    for e in evaluations:
        p = e.plagiarism_score
        if p >= 90:
            plag_ranges['90-100'] += 1
        elif p >= 70:
            plag_ranges['70-89'] += 1
        elif p >= 50:
            plag_ranges['50-69'] += 1
        else:
            plag_ranges['0-49'] += 1

    return jsonify({
        'score_distribution': score_ranges,
        'assignment_stats': assignment_stats,
        'plagiarism_distribution': plag_ranges,
        'total_evaluations': len(evaluations)
    })
